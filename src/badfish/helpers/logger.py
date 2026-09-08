import json
import os
import sys
from io import StringIO

import yaml
from rich.console import Console as RichConsole

try:
    # Python 3.7 and newer, fast reentrant implementation
    # without task tracking (not needed for that when logging)
    from queue import SimpleQueue as Queue
except ImportError:
    from queue import Queue
from logging.handlers import QueueHandler, QueueListener

from logging import (
    Formatter,
    FileHandler,
    DEBUG,
    INFO,
    ERROR,
    StreamHandler,
    getLogger,
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class BadfishSafeLoader(yaml.SafeLoader):
    """SafeLoader that keeps YAML timestamps as strings.

    Real iDRAC firmware data carries ReleaseDate values such as
    ``0000-00-00T00:00:00Z``. PyYAML's default timestamp constructor converts
    these to ``datetime`` which raises ``ValueError: year 0 is out of range``.
    Returning the raw scalar keeps the value a string and avoids the crash.
    """


BadfishSafeLoader.add_constructor(
    "tag:yaml.org,2002:timestamp",
    lambda loader, node: loader.construct_scalar(node),
)


def _safe_load(message):
    """YAML load using :class:`BadfishSafeLoader` (timestamps stay strings)."""
    return yaml.load(message, Loader=BadfishSafeLoader)


class BadfishHandler(StreamHandler):
    def __init__(self, format_flag=False):
        StreamHandler.__init__(self)
        self.messages = {}
        self.formatted_msg = []
        self.output_dict = dict()
        self.structured = {}
        self.host = None
        self.format_flag = format_flag

    def emit(self, record):
        if not self.format_flag:
            self.formatted_msg.append(self.formatter.format(record))
            return

        if getattr(record, "is_table", False):
            return

        # Structured records (e.g. check-boot) are preferred over re-parsing
        # the human log text when generating json/yaml output.
        obj = getattr(record, "obj", None)
        if obj is not None:
            self.structured[record.name] = obj

        if record.levelno == INFO and record.msg != "*" * 48:
            if record.name not in self.messages:
                self.messages.update({record.name: record.msg + "\n"})
            else:
                self.messages[record.name] += record.msg + "\n"
        elif record.levelno == ERROR:
            self.output_dict = {"error": True, "error_msg": record.msg}

    def parse(self):
        try:
            if self.host:
                host_name = self.host.strip().split(".")[0]
                structured = self.structured.get(host_name)
                if structured is not None:
                    self.output_dict.update({self.host: structured.copy()})
                    self.host = None
                    return
                # Ensure the message is properly formatted as YAML by wrapping values in quotes
                message = self.messages.get(host_name)
                if not message:
                    self.output_dict = {"unsupported_command": True}
                    self.host = None
                    return
                # Try to parse as is first
                try:
                    new_dict = _safe_load(message)
                except yaml.YAMLError:
                    # If parsing fails, try to format the value as a quoted string
                    lines = message.strip().split("\n")
                    formatted_lines = []
                    for line in lines:
                        if ":" in line:
                            key, value = line.split(":", 1)
                            value = value.strip()
                            # If value contains spaces or special characters, wrap in quotes
                            if " " in value or any(c in value for c in "{}[](),:#"):
                                value = f'"{value}"'
                            formatted_lines.append(f"{key}: {value}")
                        else:
                            formatted_lines.append(line)
                    formatted_message = "\n".join(formatted_lines)
                    new_dict = _safe_load(formatted_message)

                self.output_dict.update({self.host: new_dict.copy()})
                self.host = None
            else:
                structured = self.structured.get("badfish.helpers.logger")
                if structured is not None:
                    self.output_dict.update(structured.copy())
                    return
                message = self.messages.get("badfish.helpers.logger")
                if not message:
                    self.output_dict = {"unsupported_command": True}
                    return
                # Apply the same formatting logic for non-host messages
                try:
                    new_dict = _safe_load(message)
                except yaml.YAMLError:
                    lines = message.strip().split("\n")
                    formatted_lines = []
                    for line in lines:
                        if ":" in line:
                            key, value = line.split(":", 1)
                            value = value.strip()
                            if " " in value or any(c in value for c in "{}[](),:#"):
                                value = f'"{value}"'
                            formatted_lines.append(f"{key}: {value}")
                        else:
                            formatted_lines.append(line)
                    formatted_message = "\n".join(formatted_lines)
                    new_dict = _safe_load(formatted_message)

                self.output_dict.update(new_dict.copy())
        except (yaml.YAMLError, ValueError):
            self.output_dict = {"unsupported_command": True}

    def diff(self):
        if self.output_dict.get("error"):
            return f"ERROR - {self.output_dict.get('error_msg')}"

        # F4: only compare across exactly two hosts, each a dict of firmware rows.
        if len(self.output_dict) != 2:
            return "{}"
        (host_first, first), (host_second, second) = self.output_dict.items()
        if not isinstance(first, dict) or not isinstance(second, dict):
            return "{}"

        diff_dict = {host_first: {}, host_second: {}}
        pairs = []
        for i in first:
            if not isinstance(first[i], dict):
                continue
            for j in second:
                if not isinstance(second[j], dict):
                    continue
                # .get() so rows missing SoftwareId/Version/Name don't raise;
                # skip pairs that cannot be matched by SoftwareId.
                first_sid = first[i].get("SoftwareId")
                second_sid = second[j].get("SoftwareId")
                if first_sid is None or second_sid is None or first_sid != second_sid:
                    continue
                if first_sid == 0:
                    continue
                # Skip pairs that lack a Version to compare.
                if first[i].get("Version") is None or second[j].get("Version") is None:
                    continue
                # Compare via str() so YAML floats (e.g. 3.57) resolve identically.
                if str(first[i].get("Version")) == str(second[j].get("Version")):
                    continue
                diff_dict[host_first].update(
                    {
                        i: {
                            "Version": first[i].get("Version"),
                            "Name": first[i].get("Name"),
                        }
                    }
                )
                diff_dict[host_second].update(
                    {
                        j: {
                            "Version": second[j].get("Version"),
                            "Name": second[j].get("Name"),
                        }
                    }
                )
                pairs.append((i, j))

        if diff_dict[host_first] == {}:
            return "{}"
        output = ""
        formatted = json.dumps(diff_dict[host_first], indent=4, sort_keys=False, default=str)
        len_first = (max(len(line) for line in formatted.splitlines())) + 10
        output += f"{host_first}:".ljust(len_first)
        output += f"{host_second}:\n"
        for i, j in pairs:
            output += f"{i}".ljust(len_first)
            output += f"{j}\n"
            output += f"\t- Name: {(diff_dict[host_first][i])['Name']}".ljust(len_first)
            output += f"\t- Name: {(diff_dict[host_second][j])['Name']}\n"
            output += f"\t- Version: {(diff_dict[host_first][i])['Version']}".ljust(len_first)
            output += f"\t- Version: {(diff_dict[host_second][j])['Version']}\n"
        return output

    def output(self, output_type, host_order=None):
        if output_type == "json":
            return json.dumps(self.output_dict, indent=4, sort_keys=False, default=str)
        elif output_type == "yaml":
            return yaml.dump(
                self.output_dict,
                sort_keys=False,
                indent=4,
                default_flow_style=False,
                Dumper=NoAliasDumper,
            )
        else:
            if len(host_order) > 1:
                logger_handle = self.formatted_msg[-1].split()[0].strip("[]")
                host_order.update({logger_handle: sys.maxsize})
                sorted_msg = [
                    x
                    for x in sorted(
                        self.formatted_msg,
                        key=lambda y: host_order[y.split()[0].strip("[]")],
                    )
                ]
            else:
                sorted_msg = self.formatted_msg
            return "\n".join(sorted_msg)


_LEVEL_MARKUP = {
    "DEBUG": "[dim cyan]DEBUG[/dim cyan]",
    "INFO": "[green]INFO[/green]",
    "WARNING": "[yellow]WARNING[/yellow]",
    "ERROR": "[bold red]ERROR[/bold red]",
    "CRITICAL": "[bold red]CRITICAL[/bold red]",
}


class BadfishFormatter(Formatter):
    def __init__(self, fmt, use_color=True):
        super().__init__(fmt)
        self.use_color = use_color
        self._colors = self._build_colors() if use_color else {}

    def _build_colors(self):
        buf = StringIO()
        # no_color=False overrides NO_COLOR env var: we've already decided to
        # use color (use_color=True gate), so the builder must emit ANSI codes.
        console = RichConsole(
            file=buf,
            highlight=False,
            markup=True,
            force_terminal=True,
            no_color=False,
            color_system="standard",
        )
        colors = {}
        for level, markup in _LEVEL_MARKUP.items():
            buf.seek(0)
            buf.truncate(0)
            console.print(markup, end="")
            padding = " " * max(0, 8 - len(level))
            colors[level] = buf.getvalue() + padding
        return colors

    def format(self, record):
        if getattr(record, "is_table", False):
            return record.getMessage()
        if not self.use_color:
            return super().format(record)
        original = record.levelname
        record.levelname = self._colors.get(original, f"{original:<8}")
        result = super().format(record)
        record.levelname = original
        return result


class BadfishLogger:
    def __init__(self, verbose=False, multi_host=False, log_file=None, output=None, console=None):
        self.log_level = DEBUG if verbose else INFO
        self.multi_host = multi_host
        self.log_file = log_file

        _host_name_tag = "[%(name)s] " if self.multi_host else ""
        _format_str = f"{_host_name_tag}- %(levelname)-8s - %(message)s"
        _file_format_str = f"%(asctime)-12s: {_host_name_tag}- %(levelname)-8s - %(message)s"

        use_color = bool(console and console.is_terminal and not console.no_color)
        console_formatter = BadfishFormatter(_format_str, use_color=use_color)

        self.badfish_handler = BadfishHandler(True if output else False)
        self.badfish_handler.setFormatter(console_formatter)
        self.badfish_handler.setLevel(INFO)

        _queue = Queue()
        self.queue_listener = QueueListener(_queue, self.badfish_handler)
        self.queue_handler = QueueHandler(_queue)

        self.logger = getLogger(__name__)
        self.logger.addHandler(self.queue_handler)
        self.logger.setLevel(self.log_level)

        self.queue_listener.start()

        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            self.file_handler = FileHandler(self.log_file)
            self.file_handler.setFormatter(Formatter(_file_format_str))
            self.file_handler.setLevel(self.log_level)
            self.queue_listener.handlers = self.queue_listener.handlers + (self.file_handler,)
