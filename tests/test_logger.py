import os
import tempfile
from logging import INFO, ERROR, DEBUG, WARNING, LogRecord

from badfish.helpers.logger import BadfishHandler, BadfishFormatter, BadfishLogger
import yaml
from unittest.mock import patch, MagicMock


class TestBadfishHandler:
    def test_emit_unformatted_appends_formatted_msg(self):
        handler = BadfishHandler(format_flag=False)
        handler.setFormatter(None)
        record = LogRecord(
            name="badfish.helpers.logger",
            level=INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )

        # If no formatter, logging module will access handler.formatter, we emulate format() result
        class DummyFormatter:
            def format(self, rec):
                return f"[{rec.name}] - INFO - {rec.msg}"

        handler.formatter = DummyFormatter()
        handler.emit(record)
        assert handler.formatted_msg == ["[badfish.helpers.logger] - INFO - hello"]

    def test_emit_formatted_collects_messages_and_error(self):
        handler = BadfishHandler(format_flag=True)
        record_info = LogRecord(
            name="host1",
            level=INFO,
            pathname=__file__,
            lineno=1,
            msg="key: value",
            args=(),
            exc_info=None,
        )
        record_err = LogRecord(
            name="host1",
            level=ERROR,
            pathname=__file__,
            lineno=2,
            msg="boom",
            args=(),
            exc_info=None,
        )
        handler.emit(record_info)
        handler.emit(record_err)
        assert handler.messages["host1"] == "key: value\n"
        assert handler.output_dict == {"error": True, "error_msg": "boom"}

    def test_emit_formatted_ignores_separator_line(self):
        handler = BadfishHandler(format_flag=True)
        record_sep = LogRecord(
            name="host1",
            level=INFO,
            pathname=__file__,
            lineno=3,
            msg="*" * 48,
            args=(),
            exc_info=None,
        )
        handler.emit(record_sep)
        assert handler.messages == {}

    def test_parse_with_host_builds_output_dict(self):
        handler = BadfishHandler(format_flag=True)
        handler.host = "host1.domain"
        handler.messages["host1"] = "a: 1\nb: 2\n"
        handler.parse()
        assert handler.output_dict == {"host1.domain": {"a": 1, "b": 2}}

    def test_parse_without_host_uses_module_name_key(self):
        handler = BadfishHandler(format_flag=True)
        handler.messages["badfish.helpers.logger"] = "x: 10\ny: test\n"
        handler.parse()
        assert handler.output_dict == {"x": 10, "y": "test"}

    def test_parse_unsupported_yaml_sets_flag(self):
        handler = BadfishHandler(format_flag=True)
        handler.host = "host1"
        # Intentionally malformed YAML that still fails after formatting
        handler.messages["host1"] = "- a: 1\n  - b: 2\n"
        handler.parse()
        assert handler.output_dict == {"unsupported_command": True}

    def test_parse_yamlerror_path_via_patch(self):
        handler = BadfishHandler(format_flag=True)
        handler.host = "hostx"
        handler.messages["hostx"] = "key: value\n"
        with patch("badfish.helpers.logger._safe_load", side_effect=[yaml.YAMLError("bad1"), yaml.YAMLError("bad2")]):
            handler.parse()
        assert handler.output_dict == {"unsupported_command": True}

    def test_parse_yamlerror_path_via_patch_no_host(self):
        handler = BadfishHandler(format_flag=True)
        # No host set, exercise the else branch
        handler.messages["badfish.helpers.logger"] = "key: value\n"
        with patch("badfish.helpers.logger._safe_load", side_effect=[yaml.YAMLError("bad1"), yaml.YAMLError("bad2")]):
            handler.parse()
        assert handler.output_dict == {"unsupported_command": True}

    def test_parse_zero_date_release_date_stays_string(self):
        handler = BadfishHandler(format_flag=True)
        handler.messages["badfish.helpers.logger"] = (
            "Installed-0-16.25.40.62:\n"
            "    Id: Installed-0-16.25.40.62\n"
            "    Name: Mellanox ConnectX-5\n"
            "    ReleaseDate: 0000-00-00T00:00:00Z\n"
            "    SoftwareId: 0\n"
            "    Version: 16.25.40.62\n"
        )
        handler.parse()
        row = handler.output_dict["Installed-0-16.25.40.62"]
        assert row["ReleaseDate"] == "0000-00-00T00:00:00Z"

    def test_parse_missing_message_sets_error_marker(self):
        handler = BadfishHandler(format_flag=True)
        # No INFO message and no structured data must not raise (F13).
        handler.parse()
        assert handler.output_dict == {"unsupported_command": True}

    def test_parse_uses_structured_check_boot_data(self):
        handler = BadfishHandler(format_flag=True)
        handler.structured["badfish.helpers.logger"] = {
            "BootOrder": ["NIC.Integrated.1-1-1"],
            "HostType": "foreman",
        }
        handler.parse()
        assert handler.output_dict == {"BootOrder": ["NIC.Integrated.1-1-1"], "HostType": "foreman"}

    def test_emit_stores_structured_obj(self):
        handler = BadfishHandler(format_flag=True)
        record = LogRecord(
            name="badfish.helpers.logger",
            level=WARNING,
            pathname=__file__,
            lineno=1,
            msg="Current boot order is set to: foreman.",
            args=(),
            exc_info=None,
        )
        record.obj = {"BootOrder": ["NIC.Integrated.1-1-1"], "HostType": "foreman"}
        handler.emit(record)
        assert handler.structured["badfish.helpers.logger"] == {
            "BootOrder": ["NIC.Integrated.1-1-1"],
            "HostType": "foreman",
        }

    def test_diff_returns_error_if_error_flag_set(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {"error": True, "error_msg": "oops"}
        assert handler.diff() == "ERROR - oops"

    def test_diff_formats_version_differences(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {
            "hostA": {
                "pkg1": {"SoftwareId": 1, "Version": "1.0", "Name": "Pkg One"},
                "pkg2": {"SoftwareId": 2, "Version": "2.0", "Name": "Pkg Two"},
            },
            "hostB": {
                "pkgA": {"SoftwareId": 1, "Version": "1.1", "Name": "Pkg One"},
                "pkgB": {"SoftwareId": 2, "Version": "2.0", "Name": "Pkg Two"},
            },
        }
        out = handler.diff()
        assert "hostA:" in out and "hostB:" in out
        assert "Pkg One" in out and "1.0" in out and "1.1" in out

    def test_diff_returns_empty_when_no_differences(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {
            "h1": {"a": {"SoftwareId": 1, "Version": "1", "Name": "A"}},
            "h2": {"b": {"SoftwareId": 1, "Version": "1", "Name": "A"}},
        }
        assert handler.diff() == "{}"

    def test_diff_tolerates_zero_hosts(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {}
        assert handler.diff() == "{}"

    def test_diff_tolerates_single_host(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {
            "h1": {"a": {"SoftwareId": 1, "Version": "1", "Name": "A"}},
        }
        assert handler.diff() == "{}"

    def test_diff_tolerates_missing_software_id(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {
            "h1": {"a": {"Version": "1", "Name": "A"}},
            "h2": {"b": {"Version": "2", "Name": "B"}},
        }
        assert handler.diff() == "{}"

    def test_diff_tolerates_missing_version(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {
            "h1": {"a": {"SoftwareId": 1, "Name": "A"}},
            "h2": {"b": {"SoftwareId": 1, "Name": "B"}},
        }
        assert handler.diff() == "{}"

    def test_output_json_and_yaml(self):
        handler = BadfishHandler(format_flag=True)
        handler.output_dict = {"a": 1, "b": "x"}
        json_out = handler.output("json")
        yaml_out = handler.output("yaml")
        assert "\n" in json_out and json_out.strip().startswith("{")
        assert "a: 1" in yaml_out and "b: x" in yaml_out

    def test_output_text_sorting_by_host_order(self):
        handler = BadfishHandler(format_flag=False)
        handler.formatted_msg = [
            "[hostB] - INFO - msg-2",
            "[hostA] - INFO - msg-1",
            "[hostC] - INFO - msg-3",
        ]
        # The last message hostC will be assigned sys.maxsize and sorted last
        host_order = {"hostA": 0, "hostB": 1}
        out = handler.output("text", host_order)
        lines = out.splitlines()
        assert lines == [
            "[hostA] - INFO - msg-1",
            "[hostB] - INFO - msg-2",
            "[hostC] - INFO - msg-3",
        ]

    def test_output_text_without_sorting_when_single_host_order(self):
        handler = BadfishHandler(format_flag=False)
        handler.formatted_msg = [
            "[h2] - INFO - m2",
            "[h1] - INFO - m1",
        ]
        out = handler.output("text", {"h1": 0})
        assert out.splitlines() == ["[h2] - INFO - m2", "[h1] - INFO - m1"]

    def test_emit_skips_is_table_record_in_format_mode(self):
        handler = BadfishHandler(format_flag=True)
        record = LogRecord(
            name="host1",
            level=INFO,
            pathname=__file__,
            lineno=1,
            msg="┌─table─┐",
            args=(),
            exc_info=None,
        )
        record.is_table = True
        handler.emit(record)
        assert handler.messages == {}
        assert handler.formatted_msg == []


class TestBadfishLogger:
    def test_logger_levels_and_multi_host_formatting(self):
        logger = BadfishLogger(verbose=False, multi_host=True)
        logger.logger.info("hello world")
        # Drain the queue to handler
        logger.queue_listener.stop()
        # Expect that the formatted message captured the emitted text
        msgs = logger.badfish_handler.formatted_msg
        assert any("hello world" in m for m in msgs)

    def test_logger_file_handler_attached(self):
        fd, path = tempfile.mkstemp(prefix="badfish-log-", suffix=".log")
        os.close(fd)
        try:
            logger = BadfishLogger(verbose=True, multi_host=False, log_file=path)
            assert any(getattr(h, "baseFilename", None) == path for h in logger.queue_listener.handlers)
            logger.queue_listener.stop()
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def test_logger_creates_missing_log_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "sub", "dir", "bad.log")
            logger = BadfishLogger(verbose=False, multi_host=False, log_file=log_path)
            try:
                assert os.path.isdir(os.path.join(tmp, "sub", "dir"))
            finally:
                logger.queue_listener.stop()

    def test_logger_verbose_and_output_flag_behavior(self):
        logger = BadfishLogger(verbose=True, multi_host=False, output=True)
        assert logger.logger.level == DEBUG
        # badfish_handler should be in formatted parsing mode when output is set
        assert logger.badfish_handler.format_flag is True
        logger.queue_listener.stop()


class TestBadfishFormatter:
    def _make_record(self, level_name, level_no, msg="test message"):
        return LogRecord(
            name="badfish.helpers.logger",
            level=level_no,
            pathname=__file__,
            lineno=1,
            msg=msg,
            args=(),
            exc_info=None,
        )

    def test_colored_formatter_embeds_ansi_for_known_levels(self):
        fmt = BadfishFormatter("- %(levelname)-8s - %(message)s")
        for level_name, level_no in [("INFO", INFO), ("ERROR", ERROR), ("DEBUG", DEBUG)]:
            record = self._make_record(level_name, level_no)
            result = fmt.format(record)
            assert "\033[" in result, f"Expected ANSI codes for {level_name}"
            assert "test message" in result

    def test_colored_formatter_restores_levelname(self):
        fmt = BadfishFormatter("- %(levelname)-8s - %(message)s")
        record = self._make_record("WARNING", 30)
        fmt.format(record)
        assert record.levelname == "WARNING"

    def test_logger_uses_colored_formatter_when_tty(self):
        console = MagicMock()
        console.is_terminal = True
        console.no_color = False
        logger = BadfishLogger(verbose=False, multi_host=False, console=console)
        logger.logger.info("colorful")
        logger.queue_listener.stop()
        msgs = logger.badfish_handler.formatted_msg
        assert any("\033[" in m for m in msgs), "Expected ANSI codes in TTY output"
        assert any("colorful" in m for m in msgs)

    def test_logger_uses_plain_formatter_when_non_tty(self):
        console = MagicMock()
        console.is_terminal = False
        console.no_color = False
        logger = BadfishLogger(verbose=False, multi_host=False, console=console)
        logger.logger.info("plain")
        logger.queue_listener.stop()
        msgs = logger.badfish_handler.formatted_msg
        assert any("\033[" not in m for m in msgs)
        assert any("plain" in m for m in msgs)

    def test_logger_no_color_env_disables_colors(self):
        console = MagicMock()
        console.is_terminal = True
        console.no_color = True  # simulates NO_COLOR env var
        logger = BadfishLogger(verbose=False, multi_host=False, console=console)
        logger.logger.info("respect no_color")
        logger.queue_listener.stop()
        msgs = logger.badfish_handler.formatted_msg
        assert all("\033[" not in m for m in msgs)
        assert any("respect no_color" in m for m in msgs)

    def test_logger_uses_plain_formatter_without_console(self):
        logger = BadfishLogger(verbose=False, multi_host=False)
        logger.logger.info("no console")
        logger.queue_listener.stop()
        msgs = logger.badfish_handler.formatted_msg
        assert all("\033[" not in m for m in msgs)
        assert any("no console" in m for m in msgs)

    def test_is_table_record_bypasses_formatter(self):
        fmt = BadfishFormatter("- %(levelname)-8s - %(message)s", use_color=False)
        record = self._make_record("INFO", INFO, msg="┌─table─┐")
        record.is_table = True
        result = fmt.format(record)
        assert result == "┌─table─┐"
        assert "INFO" not in result
