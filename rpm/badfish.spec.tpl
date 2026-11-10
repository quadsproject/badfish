%global project badfish
%global org     quadsproject
%global sum     Tool for managing bare-metal systems via the Redfish API
%global desc    Badfish is a vendor-agnostic, redfish-based API tool used to consolidate \
management of IPMI and out-of-band interfaces for common server hardware \
vendors.  Badfish is also a popular song from Sublime, this may be a \
coincidence – are you a badfish too?


Name:           %{project}
Version:        @VERSION@
Release:        @RELEASE@%{?dist}
Summary:        %{sum}

License:        GPL-3.0-or-later and MIT
URL:            https://github.com/%{org}/%{project}
Source:         %{url}/releases/download/v%{version}/badfish-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
# Emulator generates a self-signed TLS cert via the openssl CLI for %check.
BuildRequires:  openssl
# Test dependencies
BuildRequires:  python3dist(pytest)
BuildRequires:  python3dist(pytest-asyncio)
BuildRequires:  python3dist(pyyaml)
BuildRequires:  python3dist(aiohttp)
Provides:       badfish = %{version}-%{release}
# The emulator subcommand (badfish.emulator.run_daemon) shells out to openssl
# to generate its self-signed TLS cert on first run.
Requires:       openssl

%description
%{desc}

%prep
%autosetup -n %{name}-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files -l %{project}

%check
%pytest

%files -n %{name} -f %{pyproject_files}
%doc README.md
%{_bindir}/%{project}

%changelog
* @DATE@ Gonzalo Rafuls <gonza@redhat.com> - @VERSION@-@RELEASE@
- built from upstream, changelog ignored
