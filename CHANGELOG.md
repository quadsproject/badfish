# CHANGELOG


## v1.7.0 (2026-09-11)

### Bug Fixes

- Black-format emulator.py and main.py
  ([`bf688cb`](https://github.com/quadsproject/badfish/commit/bf688cbd1d2df0c7c4ef3f874b027e05613a9869))

Run black to fix the two lint errors that fail the repo-wide Black check on development: expand the
  state.jobs[job_id] dict literal (over 120 chars) and collapse the parenthesized uloc expression to
  one line.

fixes: https://github.com/quadsproject/badfish/issues/556

- Build container images from checked-out code, not cloned master
  ([`d6e5653`](https://github.com/quadsproject/badfish/commit/d6e565396dd86073aee967e197bdf0bd241fee5f))

The default Dockerfile ran 'git clone https://github.com/quadsproject/badfish' with no -b flag, so
  it pulled the repository default branch (master) regardless of what the CI checkout had. The
  development-build workflow therefore published a master/v1.6.0 image as
  quay.io/quads/badfish:development, which lacked development features like the built-in Redfish
  emulator.

Build from the already-checked-out context instead (COPY . /badfish + WORKDIR /badfish). Both
  development-build and production-release workflows already actions/checkout the target ref, so
  this removes the default-branch dependence and the clone race. Added a minimal .dockerignore to
  keep .git and python caches out of the build context.

- Declare openssl dep so RPM %check can run the emulator tests
  ([`fe01c2b`](https://github.com/quadsproject/badfish/commit/fe01c2bc7372367f6257ec4afa926b631b753a26))

The emulator subcommand shells out to openssl to generate its self-signed TLS cert on first run.
  Without openssl in BuildRequires/Requires the rpmbuild %check step (pytest) fails the 3 emulator
  tests with 'openssl not found'.

Add openssl to BuildRequires (for %check) and Requires (runtime), and to the dnf install list in the
  rpmlint workflow.

- Drop unused git install and stale Dockerfiles
  ([`e5e9946`](https://github.com/quadsproject/badfish/commit/e5e99468c674db404513a6540dea40b82f8b64a9))

The image now builds from the checked-out context instead of cloning the repo, so git is unused at
  build and runtime. Dockerfile_dev and Dockerfile_local are not referenced by any workflow or
  documentation, so remove them.

- Harden formatted output parsing and check-boot JSON
  ([`578b280`](https://github.com/quadsproject/badfish/commit/578b2800b924fc2f12f3648976623e987c75e36f))

- F3: timestamp-string YAML loader at all four parse() load sites so zero-date ReleaseDate
  (0000-00-00T00:00:00Z) stays a string instead of raising ValueError in yaml.safe_load; ValueError
  added to outer except. - F4: defensive diff() tolerates 0/1 hosts, missing SoftwareId/Version,
  compares Version via str() and avoids zip truncation. - F9: BadfishLogger creates the parent dir
  of --log before FileHandler. - F11/F13: emit structured check-boot data (BootOrder/HostType) and
  guard parse() against missing messages so -o json --check-boot is sensible.

Fixes #559 #560 #565 #567 #570

- Harden multi-attribute BIOS parsing and skip no-op PATCH
  ([`ef571da`](https://github.com/quadsproject/badfish/commit/ef571daf3cb6dda78794c4e5f32cb32e89bc3d3c))

Follow-up from independent and adversarial review of the PR: - reject duplicate --attribute-value
  names instead of silently last-wins - error when --attribute-value is mixed with legacy
  --attribute/--value - require --set-bios-attribute when --attribute-value is used (no silent
  no-op) - validate pairs before any session/network work so bad syntax fails fast - resolve
  attributes to the registry canonical AttributeName before the current-value lookup and PATCH (odd
  casing no longer misreported) - skip the PATCH and reboot entirely when every value is already in
  the desired state - pin single-PATCH / no-PATCH counts and add edge-case tests

- Idrac10 virtual media and OS deployment paths
  ([`f7af2a8`](https://github.com/quadsproject/badfish/commit/f7af2a899cc778d9f2fdfa9ceed5e9165b144c74))

Dell 17G hosts (R670, iDRAC10) fail virtual media cleanup and OS deployment with "Could not unmount
  virtual media" and "iDRAC version installed doesn't support DellOSDeploymentService". iDRAC10
  dropped the legacy /redfish/v1/Dell OEM namespace and no longer serves the VirtualMedia collection
  under the manager resource.

Port of quadsproject/quads#723 (commit 0dd27bb4): - find_virtual_media_resource() resolves
  VirtualMedia from the manager then system resource, caching the result. Supermicro keeps VM1. -
  is_optical_media() and get_virtual_media_device() replace the [x for x in vm_config if "CD" in
  x][0] filter; a miss raises BadfishException instead of IndexError. -
  find_os_deployment_resource() tries {system}/Oem/Dell/... then the legacy /redfish/v1/Dell path,
  caching the result. The OS deployment action URIs now use the resolved resource.

fixes: https://github.com/quadsproject/quads/issues/723

- Propagate boot-to failures, join export path, guard init JSON parses
  ([`babdc03`](https://github.com/quadsproject/badfish/commit/babdc03b12f2a4219f8a2f528ea93e97d75d0129))

boot_to_type returns its boot_to result and execute_badfish folds a False result into the exit
  status. export_scp joins the export filename to the target directory instead of concatenating.
  find_systems_resource wraps both response JSON parses in the standard BadfishException guard.

- Reject case-insensitive duplicates and guard a missing BIOS registry
  ([`b13332c`](https://github.com/quadsproject/badfish/commit/b13332cfe2817cd733976c112ca21c463e6ff390))

The multi-attribute path silently dropped a value when two attributes differed only by case (e.g.
  ProcC1E and procc1e both mapped to the same canonical name). Make the duplicate check
  case-insensitive, narrow canonical-name resolution to the registry AttributeName field only, and
  raise a catchable BadfishException when the BMC does not expose a BIOS registry instead of
  crashing with a TypeError.

- **emulator**: Generate self-signed TLS cert at runtime, drop shipped private key
  ([`e13936a`](https://github.com/quadsproject/badfish/commit/e13936a4ebc7b1fca4eea1d11b8ff35c54775afa))

The emulator bundled a self-signed private key in SCM and in the wheel/RPM
  (emulator/certs/emulator.key). This removes it from the repo and from package data, and generates
  a fresh per-install localhost keypair on first run under $XDG_CACHE_HOME/badfish/emulator
  (overridable via BADFISH_EMULATOR_CERTS), so no private key ever sits in public artifacts.
  Existing certs are reused; the key is written 0600. Tests cover generation, reuse,
  missing-openssl, default-dir resolution, and the live daemon now exercises runtime generation.

- **emulator**: Serve advertised ServiceRoot resources and harden the user store
  ([`8f45d9d`](https://github.com/quadsproject/badfish/commit/8f45d9d182e1800234d9e69f2090464a7c978f0a))

The ServiceRoot advertised Chassis, TaskService and Registries, but all three 404'd, which would
  break any Redfish client that walks the link tree. Serve a Chassis collection, a TaskService
  resource with its Tasks collection, and a Registries collection. The user store is now written
  0600 (not world-readable under a default umask), uses a unique temp filename so concurrent
  instances don't race, and the throwaway default /tmp path is no longer trusted: a pre-existing
  file there (e.g. a locally planted Administrator) is ignored.

- **emulator**: Serve missing network collections, wire SCP export, close RBAC gaps
  ([`06bcf7c`](https://github.com/quadsproject/badfish/commit/06bcf7c193b5461b5342379f62789bfbf1b64bdf))

Findings from independent + contrarian review of this PR, all verified live:

- NetworkPorts / NetworkDeviceFunctions collections now served (were 500: _STATIC_URI referenced
  templates that don't exist). badfish walks these in get_network_adapters / get_nic_fqdds. -
  DellNetworkAttributes also registered on the Chassis tree (client uses /Chassis/... not
  /Systems/... for get/set_nic_attribute). - SCP export job now carries SystemConfiguration so
  export_scp completes instead of timing out; task template gains Oem.Dell.Message so import_scp's
  progress poll reads cleanly. - DetachISOImage returns 200 like real iDRAC (badfish only accepts
  200). - Last enabled Administrator cannot be demoted via RoleId (previously only disable/delete
  were guarded); roles re-resolved live so demotions take effect on existing sessions instead of a
  login-time snapshot. - Pending restart power-on task is cancelled by any later reset. -
  NetworkPorts member resources served; firmware member ids singularized; reused certs re-applied
  0600. - Tests: network collections + Chassis NIC attribute set, export/import payload asserts,
  live-RBAC demotion, restart override, end-to-end drives
  get_network_adapters/get_nic_fqdds/get_nic_attribute/detach/export_scp.

- **emulator**: Set member Id so boot-to-mac resolves devices
  ([`c181672`](https://github.com/quadsproject/badfish/commit/c181672ac4fbdb393ce17150107ab31e24dc0227))

The EthernetInterface template renders an empty Id, so badfish's boot_to_mac sees device=None and
  raises 'MAC Address does not match any of the existing'. Populate the member Id from its resource
  id so collection members (EthernetInterface, Processor, Memory) carry a real identity and
  boot-to-mac resolves the device.

Fixes #564

### Chores

- Add rpmlint to CI for RPM hygiene
  ([`3696206`](https://github.com/quadsproject/badfish/commit/369620627d94035d653caa000d5d9b06782f69aa))

Adds an rpmlint make target under rpm/ that builds the SRPM and binary noarch RPM and lints the spec
  plus both artifacts, and a GHA workflow that runs it in a fedora:latest container on PRs and
  pushes. Pivots the #312 investigation away from rpminspect, which targets binary packages and
  deviation analysis that do not apply to a noarch pure Python package.

fixes: https://github.com/quadsproject/badfish/issues/312

- Bump CI Python to a support version.
  ([`1b4cd5b`](https://github.com/quadsproject/badfish/commit/1b4cd5b7a81f2446536f4dd176da111ef87d81c4))

- Rpmlint CI also re-runs on commits, drop stray exec bit
  ([`a75bf61`](https://github.com/quadsproject/badfish/commit/a75bf6155063855ea1864f041aa07bb9b370d5ac))

Follow-up from independent review of the PR: - run the rpmlint gate on synchronize and reopened, not
  just opened/edited, so new commits pushed to the PR are actually linted - install rpm-build
  explicitly (previously only transitive) - add rpmbuild/ to rpm cleanup and .gitignore - mark the
  rpmlint target .PHONY - jobs get permissions: contents: read - main.py lost its shebang earlier;
  clear the stale executable bit (module is not a script; entry point is the badfish console script)

### Continuous Integration

- Gate rpmlint on setup.py and fail loudly on an empty package version
  ([`6a025ed`](https://github.com/quadsproject/badfish/commit/6a025ed88937c5f477e17a49b4e430314fd31ae1))

The rpm build derives VERSION from setup.py, but the paths filter omitted it, so a setup.py-only
  change would not re-trigger the gate. Also, if setuptools is unimportable the Makefile silently
  built badfish-.tar.gz with empty @VERSION@ substitutions; the version is now asserted non-empty
  before building.

- Only run the dev Quay publish from the canonical repo
  ([`400fd9c`](https://github.com/quadsproject/badfish/commit/400fd9cd30d01508110eadd57c7083841190728f))

Forks don't have the QUAY_USERNAME/QUAY_API_TOKEN secrets, so the Development Build workflow dies at
  podman login on every fork push (empty password -> 'inappropriate ioctl for device'). Gate the
  quay_dev job to this repo so forks skip it and the dev image is still published from
  quadsproject/badfish exactly as before.

- Re-run tox and lint on PR synchronize events
  ([`d373f09`](https://github.com/quadsproject/badfish/commit/d373f09258c21e15801d70f15532ecbc0d394574))

- Skip rpmlint on docs-only PRs and cancel stale runs
  ([`145e564`](https://github.com/quadsproject/badfish/commit/145e5648d140790611632d3ddda712d4ebab91f2))

paths filter keeps the RPM hygiene gate to packaging-related changes; concurrency group cancels
  superseded runs instead of queueing them.

### Documentation

- Document --ls-gpu and correct interface-key naming
  ([`b7aec96`](https://github.com/quadsproject/badfish/commit/b7aec9643477bc4767dd6ab0ef3a33da0cde6f10))

Add a Common Operations section and TOC entry for the --ls-gpu flag. Correct the interface-key
  format spec and all examples to match the shipped idrac_interfaces.yml keys, which use no
  _interfaces suffix.

- Sync README with current badfish feature set
  ([`a39074b`](https://github.com/quadsproject/badfish/commit/a39074bcb9d8dbc37a1f098db1812fe9c42358d3))

Full documentation sweep against the development branch codebase: fix TOC structure and anchors,
  document missing CLI options (--timeout, --insecure, --rack, --uloc, --blade), refresh the
  features and requirements lists, fix broken examples and typos, and update Redfish emulator
  documentation.

### Features

- Add --rack, --uloc, --blade CLI arguments for explicit host location
  ([`a59f3b2`](https://github.com/quadsproject/badfish/commit/a59f3b24d8bfad8e1d1e845258c2e3db95761083))

fixes #416

- Add AUR package and CI publishing
  ([`7f4d70e`](https://github.com/quadsproject/badfish/commit/7f4d70e44954879e19d9e6482174167e422dfc8c))

- Support setting multiple BIOS attributes in one invocation
  ([`c129012`](https://github.com/quadsproject/badfish/commit/c1290127d76052ea0386674241ddd98b5e5777e4))

The --set-bios-attribute path now accepts a repeatable --attribute-value option taking
  attribute=value pairs, so multiple BIOS attributes are staged and applied in a single operation
  and one reboot. Existing --attribute/--value usage is unchanged.

The accepted-value check is reset per attribute so an invalid value is not masked by an earlier
  accepted one, and accepted values are sent using the registry's canonical casing.

fixes: https://github.com/quadsproject/badfish/issues/393

- **emulator**: Accountservice user management with role-based RBAC
  ([`8890a54`](https://github.com/quadsproject/badfish/commit/8890a54231b41fbe53db558ac6d82bf899317ea8))

Adds the Redfish AccountService surface to the mock iDRAC: a JSON-backed user store (created at
  runtime, /tmp by default, BADFISH_EMULATOR_USERS to relocate), roles
  ReadOnly/Operator/Administrator, per-role authorization on mutating requests, and the
  last-enabled-Administrator guard. Users can be created, edited, removed and have passwords changed
  over the API, so future badfish user/RBAC client work has a stable target.

The store stays a flat JSON file rather than sqlite on purpose: the emulator is a temporal testing
  fixture, not a persistent service, and JSON keeps the state human-inspectable and aligned with the
  DMTF/sushy mockup convention. sqlite would be stdlib-safe too, but its durability/concurrency
  advantages are precisely what this throwaway scope does not need.

Also ships the account_service and account templates (previously missing), warts the e2e test off
  the shared /tmp default store, and declares template and cert package_data so the emulator
  actually runs from an installed wheel or RPM (templates were previously omitted from the build
  entirely).

- **emulator**: Add built-in Redfish emulator
  ([`183bb65`](https://github.com/quadsproject/badfish/commit/183bb6588631f7b0c4fe962eb2f64b8c39bb4b99))

Adds a mock iDRAC server so badfish can be developed and tested without bare metal. Run with
  "badfish --redfish-emulator --port 8443"; it always runs as a persistent server until interrupted.

Design: static resource shapes live as JSON templates under

src/badfish/emulator/templates, served over HTTPS by a small aiohttp app with an in-memory fake
  driver holding mutable system state. Architecture is inspired by the sushy-tools emulator
  (OpenStack, Apache-2.0), written independently for badfish under GPL-3.0-or-later.

Covers the surface badfish actually talks to: session/token auth, power and reset, one-shot boot and
  boot order, BIOS registry and attributes, jobs queue, virtual media, firmware inventory,
  processor/memory/network inventory, the Dell OS deployment service and SCP targets, and the Dell
  network attribute registry. Screenshot and network ISO actions report "not supported" so badfish
  degrades gracefully.

Default credentials are quads/quads (override with BADFISH_EMULATOR_USER and
  BADFISH_EMULATOR_PASSWORD). TLS uses a bundled self-signed test certificate, so clients should
  pass --insecure.

Tests: unit coverage of the API surface plus an end-to-end test that

runs the real badfish client against a live emulator over TLS.

- **emulator**: Jobs run then complete, unknown tasks 404
  ([`08910da`](https://github.com/quadsproject/badfish/commit/08910dab37f9bf4e2815de16eb402d9bd0fb4daf))

Per maintainer direction on review follow-ups: - Jobs report Running/0% on the first read, then
  Completed/100% on the next, so badfish's poll-and-retry job loops exercise a real lifecycle
  instead of instant success. The job-creation POST body renders without consuming a read so the
  first client poll sees the running state. - Import tasks are now tracked;
  TaskService/Tasks/<unknown> 404s like real iDRAC (badfish only polls tasks it created via SCP
  import). - RBAC intentionally left permissive: Operator may run SCP/job actions.

### Refactoring

- Canonicalize BIOS attribute names in a single pass
  ([`8d5880f`](https://github.com/quadsproject/badfish/commit/8d5880ff4fe0cc6bc57889203c6f6bce3608e469))

Grafuls (review): the nested loop was O(entries x attributes). Build a lowercase->canonical
  AttributeName map once, then resolve each supplied attribute with one lookup. Behavior unchanged
  (38 BIOS tests pass).

- **emulator**: Data-driven collections, shared body parser, job id helper
  ([`545a217`](https://github.com/quadsproject/badfish/commit/545a2176b7a734e116183f3dfe5ad65ef48620f3))

Make _collection_uri data-driven (open/closed: a new collection is a row in _COLLECTIONS, not a new
  branch), centralize the malformed-JSON 400 handling in _read_body (was 8 duplicated blocks), and
  factor the JID_ generation into _next_job_id (was 3 duplicated blocks). The extended flag for
  splitting the 919-line god-module into multiple files was deliberately deferred: the independent
  review judged a single file defensible for a dev-only mock, the module's helpers are referenced
  directly by the tests, and a physical split would churn tests and package_data for little gain.

### Testing

- Cover boot-to-type no-match exit path
  ([`68dcee3`](https://github.com/quadsproject/badfish/commit/68dcee3604d419ca5ad1e0bbf44de808c8c55e55))

- Cover structured parse guard and defensive diff branches
  ([`f8462a7`](https://github.com/quadsproject/badfish/commit/f8462a7c6f3671ad055f60eb7b8fb9569a91858d))

- **emulator**: Lift patch coverage past the codecov target
  ([`9f67459`](https://github.com/quadsproject/badfish/commit/9f6745934f0e6ae9352e88ac024c2d81b11d8721))

Codecov patch coverage on the new emulator surface was 74.45% against a 93.43% target, pulling the
  PR check red. Adds targeted tests for the member collections (NIC/CPU/DIMM), session and registry
  resources, malformed-JSON 400s on every JSON reader, ChangePassword and account PATCH/DELETE error
  paths, reset variants and BIOS/Manager actions, the Dell OEM endpoints (job queue, OS deployment,
  SCP import/export, screenshot), PATCH/DELETE fallthroughs, garbage Basic auth, corrupt-store
  recovery, and a live run_daemon smoke test plus the main() routing branch.

Two small correctness fixes surfaced while chasing coverage: the chassis Power consumption was dead
  code (shadowed by the static URI map), so it never varied with power state, and run_daemon now
  returns web.run_app() so callers can drive it. Patch coverage is now ~99%.


## v1.6.0 (2026-05-20)

### Bug Fixes

- Apply black formatting to main.py and test_vendor_detection.py
  ([`dc53480`](https://github.com/quadsproject/badfish/commit/dc534804f07d4f37f431276bfb542d7a5e77fdea))

- Clarify vendor-specific vs generic terminology in CLI help and docs
  ([`c0573d7`](https://github.com/quadsproject/badfish/commit/c0573d7094c8e601e9f4f1f06708662846f61fc7))

fixes https://github.com/quadsproject/badfish/issues/497

### Chores

- Black formatting
  ([`fcfcc85`](https://github.com/quadsproject/badfish/commit/fcfcc85d31d0925b259272eefbf1db5a07db1aac))

- Bump codecov python to supported 3.12
  ([`19d51fa`](https://github.com/quadsproject/badfish/commit/19d51fa75f6e150b3a3f7d21c1dce1150af9fd61))

### Features

- Add --timeout argument for configurable REST call timeout
  ([`f2ef943`](https://github.com/quadsproject/badfish/commit/f2ef9437861c5f693c117b80268558a5620a6e48))

resolved https://github.com/quadsproject/badfish/issues/412

- Add multi-vendor detection
  ([`ca03fd5`](https://github.com/quadsproject/badfish/commit/ca03fd5e08eca62164418a23ea9bb0c7d2d4cd80))


## v1.5.0 (2026-05-05)

### Bug Fixes

- Black formatting for tests and main
  ([`ed964de`](https://github.com/quadsproject/badfish/commit/ed964de14c46dcc8da5957c4d3e758e95c4d4996))

- Final black fixes
  ([`a524eb6`](https://github.com/quadsproject/badfish/commit/a524eb647eac756601f8b75d7ee73db6c535c325))

- Guard against empty SupportedLinkCapabilities list in list_interfaces
  ([`3a9f6c7`](https://github.com/quadsproject/badfish/commit/3a9f6c792a3e096c8272b9f1f1edc0b15fc51cd6))

### Features

- Colored log levels using rich
  ([`9c7499d`](https://github.com/quadsproject/badfish/commit/9c7499d9f2e5a3bafe8b5f016d9a2cf4eb8d3fd6))

Adds BadfishFormatter which uses rich markup to color-code log level names in terminal output.

- Rich table output for hardware inventory commands
  ([`c2ff592`](https://github.com/quadsproject/badfish/commit/c2ff592062bc6a97d1392497b75231cf0fc42bce))

### Testing

- Add coverage for is_table formatter bypass and emit skip
  ([`ae4d170`](https://github.com/quadsproject/badfish/commit/ae4d170c16848c87e6d5d56917c193f732a05217))


## v1.4.0 (2026-04-27)

### Chores

- Fix black formatting for CI.
  ([`03fc02e`](https://github.com/quadsproject/badfish/commit/03fc02e39aac3273d62303836caa7798bcf507aa))

- Fix importscp tests race condition
  ([`af074d8`](https://github.com/quadsproject/badfish/commit/af074d839f21ff229ad1c4a9bb667c3a6d746f3e))

- Migration to new repo url.
  ([`f6890c7`](https://github.com/quadsproject/badfish/commit/f6890c7ca043b6950d0b166c226ed0fd767af8fb))

### Features

- Introducing Rich for polling progress bars
  ([`b738358`](https://github.com/quadsproject/badfish/commit/b738358fefcccee43dfda31147b96edb57791837))


## v1.3.0 (2026-04-22)

### Bug Fixes

- --export-scp hang bug.
  ([`75f0fc1`](https://github.com/quadsproject/badfish/commit/75f0fc1ad6a440b7e441d529e0d30eeaed8bd507))

* export_scp method polling loop 'continue' statement was nested inside an unnecessary 'else:' block
  after the timeout check. This made the control flow inconsistent with the working import_scp()
  method.

fixes: https://github.com/redhat-performance/badfish/issues/499

- Add fallback / warn intelligence for XX710 NIC
  ([`a726de9`](https://github.com/quadsproject/badfish/commit/a726de906438b0d051a880b3f2f1398da2a5be04))

* We think intel XX710 may not be able to do 128 VRF * Add proper warning but don't fail.

- Refactor create_job to use _extract_job_id_from_response
  ([`28cca05`](https://github.com/quadsproject/badfish/commit/28cca050456d63a06c777fb10a874b989b84be88))

* try not to go too crazy with pragma no cover

- Resolve export_scp hanging at low percentages due to iDRAC API caching bug
  ([`ecb03a2`](https://github.com/quadsproject/badfish/commit/ecb03a21e4433723b58bfdef8d8abaf939bac7d2))

* making additional fixes here and testing, we were good but tinkered too much with control flow
  mechanisms

- Resort back to a simpler approach.
  ([`b91a73a`](https://github.com/quadsproject/badfish/commit/b91a73afb9d9a64b5363d744722d3bb9205c98fb))

* revert back to a less aggress and simpler approach

- Sriov set nic attributes dont persist on reboot.
  ([`da0ef9e`](https://github.com/quadsproject/badfish/commit/da0ef9e6ba83d263ffd8d763f1602746a5ab42a0))

fixes: https://github.com/redhat-performance/badfish/issues/523

### Chores

- Add more SSL test coverage
  ([`0621a67`](https://github.com/quadsproject/badfish/commit/0621a6798b714d942c606a73595b1484673404db))

- Add poll_helpers test
  ([`b1db697`](https://github.com/quadsproject/badfish/commit/b1db697958fabcd89c62c041a698e7173b3473d0))

- Address code review feedback
  ([`26223b9`](https://github.com/quadsproject/badfish/commit/26223b94caaf32132f611ccc84e6b28d868f690d))

- Address code review points, DRY.
  ([`cf8a454`](https://github.com/quadsproject/badfish/commit/cf8a45470963c35ecfdbe881bba97b9a93a0924a))

- Adust tests and PR feedback, increase default retries to 30.
  ([`e1516e6`](https://github.com/quadsproject/badfish/commit/e1516e6d2586f27348eeb3cab53ca5791e3a294a))

* essentially 2.7 minutes may not be enough time to poll idrac (15x retries). Increasing this to 30
  retries or just over 5min.

- Black fixes and flake8
  ([`66158ca`](https://github.com/quadsproject/badfish/commit/66158ca6b4bc2e06b2d5c3cb9d745e11369c1b02))

- Bump CI python version
  ([`7a73d7a`](https://github.com/quadsproject/badfish/commit/7a73d7aebce42489b0a077edd818689345985893))

- Fix codecov
  ([`cfe2f71`](https://github.com/quadsproject/badfish/commit/cfe2f71f596ec89c2401233e25cae7abaf6fd6fe))

- Fix formatting in GHA lint.yml
  ([`a2419d5`](https://github.com/quadsproject/badfish/commit/a2419d5c65364aa4fb726031795cedbb23ad9eec))

- Fix test with duplicate 75% response where it's skipped
  ([`69e7c2c`](https://github.com/quadsproject/badfish/commit/69e7c2c33d682f6da9faf2772cceaacaaf003a88))

- Fix tests again
  ([`2dd9971`](https://github.com/quadsproject/badfish/commit/2dd997110c41ad23f31158f7d9bb3cbe38de86b8))

- Fix tests, add doc mention
  ([`f80b915`](https://github.com/quadsproject/badfish/commit/f80b91539b55ecb2d00dab1569b7ea807f918290))

- Further fix test coverage
  ([`f3e118a`](https://github.com/quadsproject/badfish/commit/f3e118a744cc12df956254a57630e57842fc7189))

- Further test fixes
  ([`3d89b25`](https://github.com/quadsproject/badfish/commit/3d89b25c1739370d5a864887db9bf41ab8813ec6))

- Further tweak tests
  ([`ddfa57e`](https://github.com/quadsproject/badfish/commit/ddfa57e640a3e067f6a99ec713f4daac85c9b3e3))

- Hopefully fix rest of tests
  ([`6fdc73c`](https://github.com/quadsproject/badfish/commit/6fdc73cdeb3734c836eee9529408884ad9040f8e))

- Make codecov happy
  ([`918d99c`](https://github.com/quadsproject/badfish/commit/918d99c49629b5a056948f76788ed7d7ad32b9b5))

- Simplify tests
  ([`6f60320`](https://github.com/quadsproject/badfish/commit/6f6032051b38ac975b2d11444e720988787c427c))

* Don't obesess over defensive / firmware status handling

- Try to eek out more test coverage
  ([`93b5e53`](https://github.com/quadsproject/badfish/commit/93b5e53d50d09aa9b043e58deb457925799dc1a7))

- Update testing coverage
  ([`6e8fb92`](https://github.com/quadsproject/badfish/commit/6e8fb92646a9108f826188158cb5046665387360))

### Features

- Add --insecure flag and SSL verification.
  ([`42b7441`](https://github.com/quadsproject/badfish/commit/42b7441190feb7a713a2601f8b198ba10b4a0b82))

fixes: https://github.com/redhat-performance/badfish/issues/499

fixes: https://github.com/redhat-performance/badfish/issues/498

* We now properly check SSL connections and offer an --insecure parameter. * export_scp hang bug:
  Fixed by discovering that Dell iDRAC API endpoints (both Tasks and Jobs) return stale/cached
  status data showing "Running" indefinitely even after the job * Add more fixes for --export-scp
  feature * Workaround: Instead of unreliable polling, we now wait 45 seconds which is more than
  enough time then fetch json. * This now fully works and is fast.

- INFO - Job for exporting server configuration successfully created. Job ID: JID_763636328050 -
  INFO - Waiting for export job to complete (typically takes 15-30 seconds)... - INFO - SCP export
  completed successfully. - INFO - Exported system configuration to file:
  ./2026-04-16_142201_targets_IDRAC-BIOS_export.json - INFO - Job for exporting server configuration
  successfully created. Job ID: JID_763636328050 - INFO - Waiting for export job to complete
  (typically takes 15-30 seconds)... - INFO - SCP export completed successfully. - INFO - Exported
  system configuration to file: ./2026-04-16_142201_targets_IDRAC-BIOS_export.json

real	0m57.349s user	0m0.409s sys	0m0.066s

- Add --version flag to CLI
  ([`215d1ea`](https://github.com/quadsproject/badfish/commit/215d1ea810dd1bd4a307d899faa6fc0306c7c152))

Resolves #525.

(cherry picked from commit fdd7b1d0058d336a509abc2d0aaf081593c9e1b8)

- Add --wait to racreset
  ([`093c005`](https://github.com/quadsproject/badfish/commit/093c00588e0ab6cdcc428f33677fd2853a9ab7fc))

fixes: https://github.com/redhat-performance/badfish/issues/450

- Refactor to include three helper functions.
  ([`2d662a5`](https://github.com/quadsproject/badfish/commit/2d662a56a129fdc2095194b30a4dd3f61095809e))

* Always be DRY'ing

Helper 1: _extract_job_id_from_response() Helper 2: _verify_job_scheduled() Helper 3:
  _monitor_and_verify_attribute_job()


## v1.2.0 (2026-02-13)

### Bug Fixes

- Apply black fixes, more test cov for nic attr
  ([`b31e537`](https://github.com/quadsproject/badfish/commit/b31e5376c9d6fbce4325634cae3667ee92404aac))

- Incorrect credentials are masked by traceback
  ([`54fa694`](https://github.com/quadsproject/badfish/commit/54fa6945063cc5cde2379855fd55074b498fc04b))

* find_session_uri masks a proper error message when someone passes incorrect credentials (either by
  vars or user/pass). * response body seems to be a JSON object and not a redfish root object and we
  are not generating a useful error, instead the user gets a traceback that masks the real cause.

before (see https://github.com/redhat-performance/badfish/issues/517)

after

-=>>PYTHONPATH="./src" python3 src/badfish/main.py -H mgmt-d23-h31-000-r650.example.com -u root -p
  awrongpassword --power-state - WARNING - Passing secrets via command line arguments can be unsafe.
  Consider using environment variables (BADFISH_USERNAME, BADFISH_PASSWORD). - ERROR - Failed to
  authenticate. Verify your credentials for mgmt-d23-h31-000-r650.example.com

* Also remove asyncio import from tests/test_main_coverage.py as it wasn't being utilized.

fixes: https://github.com/redhat-performance/badfish/issues/517

### Chores

- Address mock whitespace in tests
  ([`05b409b`](https://github.com/quadsproject/badfish/commit/05b409b293ab1e20c58f3950b659e2577c4f80f7))

- Fix debug logger typo
  ([`0116cb7`](https://github.com/quadsproject/badfish/commit/0116cb74f87f5203ca2016f6752c9c35a0210928))

- Fix indentation
  ([`073efca`](https://github.com/quadsproject/badfish/commit/073efcad3314706620ed6f4efe5f9554d080e472))

- Fix last coverage lines
  ([`f2d4637`](https://github.com/quadsproject/badfish/commit/f2d4637b36e42cd4dc16b68db279154a39225299))

- Fix tests spacing on returns
  ([`a113725`](https://github.com/quadsproject/badfish/commit/a113725d27b688d00c9b3645c7176bf1717ba2e6))

- Fully revert old_password,new_password env
  ([`3de528b`](https://github.com/quadsproject/badfish/commit/3de528bc26bb51bc527acba234f0178778063567))

- Further tests adjustment
  ([`0741776`](https://github.com/quadsproject/badfish/commit/0741776c3f7bfa4f48d21cd0e7eaf1ec3ba53e77))

- I grow weary of adjusting test intricacies
  ([`3c68a68`](https://github.com/quadsproject/badfish/commit/3c68a68739920a78522d97fa63c5a6617cfba799))

- Refactor test_main_coverage.py for black
  ([`42d4911`](https://github.com/quadsproject/badfish/commit/42d4911becd3d1090e16fa78fd2e81a2d5f5e631))

- Remove new/reset/old password handling
  ([`1e9298e`](https://github.com/quadsproject/badfish/commit/1e9298ee9c11bf2a4afcbe1e972b24be50aa0a90))

* This is clumsy and very unlikely these values will be an env variable. * Nothing keeps people from
  securing it with a temporary export but it is not in scope for using stored env vars which tend to
  be static or change rarely and thus makes more sense to concentrate on for this feature.

- Revert, fix up only affected tests
  ([`848a4e8`](https://github.com/quadsproject/badfish/commit/848a4e817007c16274e6d9fd67aa98b65cfe36d3))

- Set test vars in config.py
  ([`4ec3b1d`](https://github.com/quadsproject/badfish/commit/4ec3b1d423fe0b7c415980585349df9d0233aacb))

- Spacing again on tests
  ([`4661d74`](https://github.com/quadsproject/badfish/commit/4661d74704715cf7a4b30cfffcea6f552c2b5cf7))

- Test modifications
  ([`d3568f0`](https://github.com/quadsproject/badfish/commit/d3568f077f42f42e03fa4405dbed182eac07019e))

- Try to fix failing tests and tox
  ([`b1e14b2`](https://github.com/quadsproject/badfish/commit/b1e14b2f4e8b7e2bdde59dd3f6427dfdf8386b44))

- Try two on aligning spacing for log msgs
  ([`0a67bda`](https://github.com/quadsproject/badfish/commit/0a67bda956acada5d1043b55f925318b7b0bc222))

- Update doc examples by suggest
  ([`52f721b`](https://github.com/quadsproject/badfish/commit/52f721bb9fe714a5cc885b73c571b59098f03653))

* incorpoate some suggestions from @stephane-chazelas

- We should not need mock user/pass now
  ([`805cdad`](https://github.com/quadsproject/badfish/commit/805cdad4c3a388684f4e22f57b1bd374d6dca447))

- Whitespace and unsafe_secrets for tests
  ([`01ff58a`](https://github.com/quadsproject/badfish/commit/01ff58a0a8be85b3624da05a91d4ae55193cd038))

### Features

- Support auth via env vars
  ([`38cc4e0`](https://github.com/quadsproject/badfish/commit/38cc4e098d3371cba51072c79ebbc8d77e9d7038))

* Add these new vars for safer badfishing - BADFISH_PASSWORD - BADFISH_USERNAME -
  BADFISH_NEW_PASSWORD - BADFISH_OLD_PASSWORD

* Update venv example for PYTHONPATH

fixes: https://github.com/redhat-performance/badfish/issues/496


## v1.1.1 (2026-02-03)

### Bug Fixes

- Dockerfile versioning
  ([`1ac86a7`](https://github.com/quadsproject/badfish/commit/1ac86a758a2935bff83f9b5637960043f647fc0d))


## v1.1.0 (2026-02-03)

### Bug Fixes

- Don't pin GHA workflows
  ([`0d23853`](https://github.com/quadsproject/badfish/commit/0d23853724a404f99f76f1caa09dd4f7771164fa))

- Event_loop for strict Py314 and beyond.
  ([`a61ca94`](https://github.com/quadsproject/badfish/commit/a61ca94a360c5b820e0cb4e5ebd8258fb8a6fdf3))

related-to: https://github.com/redhat-performance/badfish/issues/480

- Production-release srpm generation
  ([`f859e1e`](https://github.com/quadsproject/badfish/commit/f859e1ecc79ec1d50b7c56de2a8a3ac7b3936774))

- Supermicro session uri on redfish v101
  ([`b6df52a`](https://github.com/quadsproject/badfish/commit/b6df52a3aba50dfa2da7b1352fe7e84f0e85da3b))

- Unified versioning for semantic-release
  ([`9d3d3bf`](https://github.com/quadsproject/badfish/commit/9d3d3bfb3667dd561c73db1ff4f2950747265ea0))

### Chores

- Fix COPR workflows
  ([`ec45870`](https://github.com/quadsproject/badfish/commit/ec4587092b619f75083701cc3e8cbc0eefff111f))

### Features

- Just testing semantic release workflow.
  ([`bee8c78`](https://github.com/quadsproject/badfish/commit/bee8c78d5a5ea9505afb5f32c9569fc43337fae1))

- Rework/refactor GHA and CI/CD.
  ([`04f4acc`](https://github.com/quadsproject/badfish/commit/04f4acc2b9911122846c05f889e729d175b573db))

* Create per-environment GHA workflows * For development and master publish quay images - remove old
  builds, perform re-tags * For master only - build new SRC rpm and push to COPR - spin and
  increment new github release - push new badfish release to Pypi * Once there is a successful push
  to master - sync changes back to development branch to prevent drift and merge conflicts.


## v1.0.7 (2026-01-29)

### Bug Fixes

- Test reqs
  ([`1c6c88b`](https://github.com/quadsproject/badfish/commit/1c6c88b2a112fcc10bdf18a0eeca347922348243))

### Features

- Add newer or updated idrac_interfaces pairs.
  ([`70a9feb`](https://github.com/quadsproject/badfish/commit/70a9febdd4fbc4fd962c3a4d495e4eec1e836ab0))


## v1.0.6 (2025-10-20)

### Continuous Integration

- Update package naming and drop Python 3.8-3.9 support
  ([`21948e1`](https://github.com/quadsproject/badfish/commit/21948e1724ac053747b1afd4da62959e71b4b74d))

### Documentation

- Fixed version naming
  ([`0249bfa`](https://github.com/quadsproject/badfish/commit/0249bfa32453fa283a26d8481e87ec5b0bcd5a76))


## v1.0.5 (2025-10-18)

### Bug Fixes

- Copr CI
  ([`e1cb31b`](https://github.com/quadsproject/badfish/commit/e1cb31b01c1bf42433037f38935b16ab1a4b6bf2))

- Copr rpm build
  ([`1d148d3`](https://github.com/quadsproject/badfish/commit/1d148d36fbc95a99bbc503c0136578e792b6d012))

- Test_nic_attr on vendor unsupported
  ([`23c778b`](https://github.com/quadsproject/badfish/commit/23c778b938508d87e1467c2afd893c521cf4095d))

### Testing

- Refactor code style and update RPM build dependencies
  ([`2712b22`](https://github.com/quadsproject/badfish/commit/2712b22f9ac8df7dc308c54816bda13160b70c8d))


## v1.0.4 (2025-10-15)

### Bug Fixes

- Better session handling
  ([`a512146`](https://github.com/quadsproject/badfish/commit/a512146d824da8f480224e6177340675bee307f2))

closes: https://github.com/redhat-performance/badfish/issues/447

- Default for custom device types on idrac_interfaces
  ([`3dba55f`](https://github.com/quadsproject/badfish/commit/3dba55fa72e03ccb380c129acaa7aedd215a52ee))

closes: https://github.com/redhat-performance/badfish/issues/446

- Json output on mapping values
  ([`79c552a`](https://github.com/quadsproject/badfish/commit/79c552a7ecd4ee616f7dd7555e81d755ad1bdc5c))

- Logger incorrect call
  ([`39295ab`](https://github.com/quadsproject/badfish/commit/39295ab830bbf2eef123a42ce59d2a8c8a562d1c))

- Move response status check before parsing JSON
  ([`a1d5b74`](https://github.com/quadsproject/badfish/commit/a1d5b74b5df134d8269f76ff4e88582babe6a565))

- Rpm copr build
  ([`5cf219e`](https://github.com/quadsproject/badfish/commit/5cf219eff7bd5273d5599ccbba74d4576c3c4e2a))

- Tests after session termination
  ([`93165f9`](https://github.com/quadsproject/badfish/commit/93165f99274e9602e0c90ad959f2dadc2a789af7))

- Tests for session mgmt
  ([`9ff16bb`](https://github.com/quadsproject/badfish/commit/9ff16bbc6717a2db5f63d301d224d3b5b669bd46))

### Build System

- Rename package from badfish to pybadfish and update build configuration
  ([`afe614d`](https://github.com/quadsproject/badfish/commit/afe614d63d71c176af6a5ff0d4b009812511a27f))

### Refactoring

- Extract configuration, exceptions, and HTTP client into separate modules
  ([`0736979`](https://github.com/quadsproject/badfish/commit/07369795c438b0318066bcf01923eb983f3df974))

- Extract HTTP client and parser into separate modules
  ([`299dc1f`](https://github.com/quadsproject/badfish/commit/299dc1fc7f17978fc84b8b88e6d4751666306910))

- Update import paths from badfish to src.badfish for consistency
  ([`8f7e28d`](https://github.com/quadsproject/badfish/commit/8f7e28def209f8bfc3cd04d8be3b57c4bd8a4fae))

### Testing

- Add comprehensive test coverage for HTTP client and logger modules
  ([`7d33ece`](https://github.com/quadsproject/badfish/commit/7d33ecee60997391b5b9ebbb3f107f190c7351f3))

- Enhance logger test coverage with YAML error handling and formatting edge cases
  ([`4260a7e`](https://github.com/quadsproject/badfish/commit/4260a7e369062edcb5e6949b26650880527a82ee))


## v1.0.3 (2025-05-22)

### Bug Fixes

- Black linting
  ([`4ed6dfc`](https://github.com/quadsproject/badfish/commit/4ed6dfce6e8e77b0279366e1d56286709c69708c))


## v1.0.2 (2025-05-12)

### Bug Fixes

- --host arg gets interpreted as --host-list
  ([`2e8b997`](https://github.com/quadsproject/badfish/commit/2e8b997a95651920aedc10e7a1869966644913a4))

closes: https://github.com/redhat-performance/badfish/issues/151

- Added libjpeg dependency
  ([`9a9225c`](https://github.com/quadsproject/badfish/commit/9a9225cdb94d6241f7c703705d3b89ba1b867674))

- Added mock for DellJobService entrypoint
  ([`fd0584a`](https://github.com/quadsproject/badfish/commit/fd0584aeec7eb41d0b7586480194264d5e7fddb7))

- Added msg for unsupported
  ([`a7c0978`](https://github.com/quadsproject/badfish/commit/a7c0978e2c6920aed8a53fdf1af9f8ae5f0637bc))

- Added pip to RPM build
  ([`af3bf92`](https://github.com/quadsproject/badfish/commit/af3bf927fab664f47b50a1cc16588897297ffd57))

- Added requirements to setup.py plus fixes from quads
  ([`dc323bf`](https://github.com/quadsproject/badfish/commit/dc323bffe96b1525ffaca4f461dbb54ca16f43d1))

- Added zlib for epel8
  ([`eae0c35`](https://github.com/quadsproject/badfish/commit/eae0c3585e89bd28f14703cec8f45b157fdd4303))

- Added zlib-devel to installrequires on rpm.spec
  ([`c7b05ee`](https://github.com/quadsproject/badfish/commit/c7b05eeeaf5a0728117d3811b5182a2f8a93f8bb))

- Additional for boot_to test
  ([`5a0333c`](https://github.com/quadsproject/badfish/commit/5a0333c240585829f9f4e2cb09faeefbe4951044))

- Additional test
  ([`9f7f41c`](https://github.com/quadsproject/badfish/commit/9f7f41c720323492946f77f42f4e08e27f6a2d98))

- Aiohttp verify_ssl
  ([`92b947a`](https://github.com/quadsproject/badfish/commit/92b947a2a8bbde5e39402eb27cf8f4fe23754b10))

- Alias compatibility
  ([`a60f615`](https://github.com/quadsproject/badfish/commit/a60f6154eef861f77414d2b2a75e6703dd6f5819))

- Allowable reset types return when not available
  ([`60c31b3`](https://github.com/quadsproject/badfish/commit/60c31b3ac49874eb1765c4e5bb3906b79faffc75))

This resolves a back trace for r640s when set type is not available

- Async_lru not working with python3.10
  ([`bfa226a`](https://github.com/quadsproject/badfish/commit/bfa226a94fc069fa962e94211c43f04c33d4bd8e))

limiting python alpine image to python 3.9

- Bad paste failing on syntax check
  ([`c6f1dea`](https://github.com/quadsproject/badfish/commit/c6f1dea742f2cbcb8c52e7eaf79f3820593bb74e))

- Better error messages for check-boot on non-supported
  ([`bd3d2a2`](https://github.com/quadsproject/badfish/commit/bd3d2a2e0bd5b0e602075590b6ba6d81a38b38fb))

if BootSources redfish API entrypoint is not available, none of of the boot order operations can be
  executed on the host.

fixes: https://github.com/redhat-performance/badfish/issues/48

- Better way to skip caching GET requests
  ([`2bb1c33`](https://github.com/quadsproject/badfish/commit/2bb1c336476d991b84d9fbf9fcf40bd5ed5605c5))

- Blacked
  ([`5a22209`](https://github.com/quadsproject/badfish/commit/5a22209b8e5e0c4fdd490577ca613ce3b43ef2fb))

- Blade host overrides
  ([`3fde784`](https://github.com/quadsproject/badfish/commit/3fde784c7261ed00c8a4dd5690c9512ede56f6d9))

- Boot_to tests
  ([`88f372e`](https://github.com/quadsproject/badfish/commit/88f372e0cde2166d40fe40c613d2307fbea93532))

- Bump codecov version to 2.1.13
  ([`6618328`](https://github.com/quadsproject/badfish/commit/661832800dce73da2ea8bfef1a259c9486cfe975))

* GHA seems to want this version now and gets mad otherwise.

- Change boot order only on valid devices
  ([`b6d83e4`](https://github.com/quadsproject/badfish/commit/b6d83e42f9b3fcc053fedc7f5286e76959facb39))

- Changed arguments for mounting virtual media
  ([`8f12e5b`](https://github.com/quadsproject/badfish/commit/8f12e5b12bf23115b7d6e798205d0cb524354180))

- Changed container references on README to point at QUAY.io
  ([`0319f98`](https://github.com/quadsproject/badfish/commit/0319f9897a5ad12b89ae5ab12203c32cf909dda1))

- Check for job_id when no id is returned
  ([`29e360b`](https://github.com/quadsproject/badfish/commit/29e360b3430205281f314245c3ad547af78d7a6c))

- Code coverage execution
  ([`03f302e`](https://github.com/quadsproject/badfish/commit/03f302e53c545bf42d87c35e192533c7aa37be0c))

- Codecov GH action
  ([`5b4dbb8`](https://github.com/quadsproject/badfish/commit/5b4dbb84feba1cf2ea70ff8a3f9da82464b7628f))

- Codecov run
  ([`bcba5ee`](https://github.com/quadsproject/badfish/commit/bcba5ee31f24df864d5cd9fd43dd6baf6097280a))

- Codecov tokenized
  ([`d055a83`](https://github.com/quadsproject/badfish/commit/d055a8301dbeec7f1d09f00534fc3d930beb95cf))

- Defaults for scp_targets
  ([`c8d1474`](https://github.com/quadsproject/badfish/commit/c8d1474e8e24c84fa24a121ead1f87b5e5b7b0c0))

- Dependabot alerts
  ([`16df98d`](https://github.com/quadsproject/badfish/commit/16df98d30d4e95b5ab72eeb008edec2ff99baeca))

- Deprecated --gif
  ([`d909eaf`](https://github.com/quadsproject/badfish/commit/d909eafe39ca63221f5f9dd4407fa2c21266a6ea))

- Dockerfile new install instructions
  ([`2af964b`](https://github.com/quadsproject/badfish/commit/2af964bb05bfb500e402906001f44422e736986b))

added dockerfile_local for local development

- Dockerfile_dev git checkout
  ([`f71a7e0`](https://github.com/quadsproject/badfish/commit/f71a7e0ed2ddff208f9488b51b5617457ee8aaa7))

- Downgrade of setuptools
  ([`4c7574b`](https://github.com/quadsproject/badfish/commit/4c7574b22bf7312524373a9e2cca19c31f03d47d))

- Fixed bug when requesting gif from turned off server
  ([`2aa2e4c`](https://github.com/quadsproject/badfish/commit/2aa2e4c209068b103405c3facf58ff44708fa9df))

closes: https://github.com/redhat-performance/badfish/issues/288

- Fixes to file handler
  ([`b44611c`](https://github.com/quadsproject/badfish/commit/b44611c22c25fa60da68476f66ffb42d8c4e11a4))

- G-chat webhook payload
  ([`6b35b29`](https://github.com/quadsproject/badfish/commit/6b35b292d0c6738f1fde9709fe2bd39a2a4e22db))

- Gha platform version
  ([`3c45e61`](https://github.com/quadsproject/badfish/commit/3c45e61ef26744f3ac55a28e52564f118639279c))

- Github actions for codecov and lint
  ([`5041c2f`](https://github.com/quadsproject/badfish/commit/5041c2f79ad609a59cbb55f5c67168f1612c40a8))

- Helpers import
  ([`5df6155`](https://github.com/quadsproject/badfish/commit/5df615511b83dd385a4d0b956311bea20a17d7fb))

- Idrac8 / R630 boot_to
  ([`ac59e80`](https://github.com/quadsproject/badfish/commit/ac59e80b1a7ea268b700b362d4b3be8d03341dce))

- Idrac_interfaces blade relocation
  ([`0335109`](https://github.com/quadsproject/badfish/commit/03351092e02e8bdb51bfd841610dc5a9c36223ed))

- Ignore extraneous whitespace in hosts file
  ([`e49039c`](https://github.com/quadsproject/badfish/commit/e49039cd3d00fa40ff0505d80e691550b15c37bc))

- Lint execution
  ([`693d485`](https://github.com/quadsproject/badfish/commit/693d4851f540d01c4e2429786e0762289c6e2876))

- Lint GHA
  ([`994fc19`](https://github.com/quadsproject/badfish/commit/994fc1909f9f5fd9d89fdd1e21c55f800158966a))

- Lint ignores
  ([`20497ad`](https://github.com/quadsproject/badfish/commit/20497ad995c1ff21fa0425bffdb6d45d684a1882))

- Make black lint suggestions less angry.
  ([`f197f36`](https://github.com/quadsproject/badfish/commit/f197f368050bad86cf50054b6f6e4b0c20c50bd6))

* Fix linter being mad about asyncio method spacing.

- Make sure git present in container
  ([`1857b8c`](https://github.com/quadsproject/badfish/commit/1857b8c545e362058ef405a0bdac01508a1656be))

- Merge conflicts
  ([`1dead4e`](https://github.com/quadsproject/badfish/commit/1dead4e23cb5663b1bd38e9c181cdbb841e2af13))

- Merge conflicts
  ([`636d4f1`](https://github.com/quadsproject/badfish/commit/636d4f147c331d70bfcadaf1fcd32c11f1420b96))

- Move get_now to helpers + cleanup
  ([`ec7d8dd`](https://github.com/quadsproject/badfish/commit/ec7d8ddfd51f15f3f71333de411cf94f06cd4b78))

- Moved container base image to quay plus refactor
  ([`796a1f1`](https://github.com/quadsproject/badfish/commit/796a1f19a29a963461f9f5e9d8fefdb65e152194))

- Moved helper to badfish src dir
  ([`b44f62b`](https://github.com/quadsproject/badfish/commit/b44f62b86d1bc850a702f2b09bdcf031290a42bc))

- Moved pr template to the correct dir
  ([`428a233`](https://github.com/quadsproject/badfish/commit/428a233b76371728048420e28597b5c4bbbf6ec1))

- Non blocking or failing on --host-list
  ([`be19cbf`](https://github.com/quadsproject/badfish/commit/be19cbf28afd0b774ca5090dda40e3e9541aec5d))

closes: https://github.com/redhat-performance/badfish/issues/388

- Output order via podman
  ([`b8c1c93`](https://github.com/quadsproject/badfish/commit/b8c1c9367e268bc567d17bff54a275111ec180d3))

closes: https://github.com/redhat-performance/badfish/issues/320

- Package rpm installation
  ([`7633382`](https://github.com/quadsproject/badfish/commit/763338219cbf268dee9953a9041c75fbae48c946))

- Package rpm installation/lint/codecov
  ([`706d097`](https://github.com/quadsproject/badfish/commit/706d097060ce713cc57dec42f5c4ef4fe7fe08c9))

- Package upload and source rpm download
  ([`f54a36d`](https://github.com/quadsproject/badfish/commit/f54a36df00b912ef98da31fd24a77a152ab8876a))

- Pip install
  ([`748fc13`](https://github.com/quadsproject/badfish/commit/748fc13a07344dcdb5c5fe3f313990053475f554))

- Pushed bad git diff
  ([`eb2c8e5`](https://github.com/quadsproject/badfish/commit/eb2c8e56dfdefe3590592c979defd5f1e3e664a1))

- Python packaging
  ([`adb4d69`](https://github.com/quadsproject/badfish/commit/adb4d692b52e7c40eb64339418d395e7a56b4519))

- Python versions for GHA
  ([`fae5f03`](https://github.com/quadsproject/badfish/commit/fae5f03802f051a6ab2aaed8eabab491a9094915))

- Readme TOC
  ([`8b955d9`](https://github.com/quadsproject/badfish/commit/8b955d9c28d8b3faed23bb3fad4ce74e69ad1689))

- Reboot-only for 740XD
  ([`2bb9694`](https://github.com/quadsproject/badfish/commit/2bb9694121104fd661583e90b77da44cf81094af))

closes: https://github.com/redhat-performance/badfish/issues/118

- Remove scheduled GHA and fix for branch name
  ([`8350462`](https://github.com/quadsproject/badfish/commit/8350462e042301e3259e0dd7957aeb9d85f526a5))

- Removed breakpoint
  ([`8eee0b4`](https://github.com/quadsproject/badfish/commit/8eee0b417473c550ec7b24b972c9ac41f37ef19b))

- Removed files definition from spec.tpl
  ([`8117a6e`](https://github.com/quadsproject/badfish/commit/8117a6e9469dd5772b360c6a0323ab3a1d16bc67))

- Removed problematic call from boot_to()
  ([`64ff289`](https://github.com/quadsproject/badfish/commit/64ff289961108fa629f5c91efc1f2998522f277f))

closes: #354

- Removed redundant method
  ([`b6129d4`](https://github.com/quadsproject/badfish/commit/b6129d487c387a3f87d483a4a44f3a2c19672eb9))

- Removed rpm build on PR
  ([`2c4b60b`](https://github.com/quadsproject/badfish/commit/2c4b60b2b844c4b20b97770b9faae94ba05fae50))

- Removed support for py3.6
  ([`c94cfa1`](https://github.com/quadsproject/badfish/commit/c94cfa168b72d168ca2e69dbdbdea231b8a8c814))

- Removed try catch
  ([`88acd3d`](https://github.com/quadsproject/badfish/commit/88acd3d5cb2efbf26fe8bb84ee1111c0c25c2dff))

- Removed unnecessary part of condition
  ([`7cb32e7`](https://github.com/quadsproject/badfish/commit/7cb32e76a99f33fbdc45b8489ae413440024ba2c))

- Reusing read_yaml
  ([`2eba02f`](https://github.com/quadsproject/badfish/commit/2eba02f33b8fe862869fe2093d12b6244dfe3a06))

- Rpm check from tox to pytest
  ([`d371ef0`](https://github.com/quadsproject/badfish/commit/d371ef098507c7501e74d79593a3960da6cefbff))

- Rpm GHA build and upload
  ([`c691ca1`](https://github.com/quadsproject/badfish/commit/c691ca1afbafdcc0cdd731913994cee6ca19986d))

- Rpm spec tmpl
  ([`d2c54fc`](https://github.com/quadsproject/badfish/commit/d2c54fc1d390f371bcd60436493bdeb64b448d8a))

- Safer url parsing
  ([`e593766`](https://github.com/quadsproject/badfish/commit/e593766fc05c12e635ac5dd70c306df7e3c84a22))

- Set nic attributes
  ([`909461d`](https://github.com/quadsproject/badfish/commit/909461d017c5562835454df5945f97b3355f15a7))

- Setup missing helpers include
  ([`c8116d7`](https://github.com/quadsproject/badfish/commit/c8116d7e0ca46d8714658e47bc1df6f19ec7f45e))

We were missing to include the helpers directory under the package definition for setuptools. Also
  refactored the logging logic to an independent logger for easier imports when using BF as a python
  library. Included .editorconfig for code styling.

- Spec.tpl and setup entrypoint
  ([`26341cc`](https://github.com/quadsproject/badfish/commit/26341cc32fd5f7dba43e82ad9685220e99c8280e))

- String formatting on power consumed
  ([`ad5e892`](https://github.com/quadsproject/badfish/commit/ad5e8924706f164926e56cb2b65ccaee9c5daf68))

- Support for uefi boot mode
  ([`94749e0`](https://github.com/quadsproject/badfish/commit/94749e02259c84850a8258c11e47e6a057dc877d))

- Test scp on test pass mocking datetime.now
  ([`9ded0bc`](https://github.com/quadsproject/badfish/commit/9ded0bc6d10cef991eb10052e90d2d6ca91b7a09))

- Test_bios_pas imports
  ([`a083308`](https://github.com/quadsproject/badfish/commit/a083308780ecb05a20958db71022fff2859cf70a))

- Tests
  ([`319f96a`](https://github.com/quadsproject/badfish/commit/319f96abfae108954fcdf60f7fe6373ea45e5173))

- Tests
  ([`b9219a4`](https://github.com/quadsproject/badfish/commit/b9219a44e1abfef3cd688c22041d3ded0d0525fe))

- Tests dependecies for tox on rpmbuild
  ([`d57208b`](https://github.com/quadsproject/badfish/commit/d57208bbecf5b998dfe7e36d229fd7713655b68c))

- Tests for boot_to and virtual_media
  ([`7ad8f43`](https://github.com/quadsproject/badfish/commit/7ad8f430873ad47c143463971b43d6b919d29a35))

- Tests import issues
  ([`2a47daa`](https://github.com/quadsproject/badfish/commit/2a47daa8d458f30383f156ff56a645f5f6832e96))

- Tox version
  ([`757f36d`](https://github.com/quadsproject/badfish/commit/757f36d6be87636a3b1e973020e0bf44e0616796))

### Code Style

- Formatting with black
  ([`6c84332`](https://github.com/quadsproject/badfish/commit/6c843322aaf5f5d5eac5fedea32537dc210afe6b))

- Formatting with black
  ([`74c1211`](https://github.com/quadsproject/badfish/commit/74c1211c8e079c2c48cad0429db5cee8e9ff7c9d))

- Formatting with black
  ([`e7c34a4`](https://github.com/quadsproject/badfish/commit/e7c34a4bf44ef72c3ebd4888afe8e2031bf99050))

- Lint fixes
  ([`bbb1680`](https://github.com/quadsproject/badfish/commit/bbb16806e52c1688d807bfc4e195e5466c3fec29))

- Removed comments and fixed import indentation, from recently added tests
  ([`549b655`](https://github.com/quadsproject/badfish/commit/549b655d138739f2df741780b12a9af8c21a8aae))

- Unnecessary if/else changed to one liner
  ([`9673797`](https://github.com/quadsproject/badfish/commit/9673797b2a1a7b9217762d2e8b144d66552ac0be))

### Continuous Integration

- Fix for create versioned tarball
  ([`47cb674`](https://github.com/quadsproject/badfish/commit/47cb674a220a93da42f686736b09a1068e72a3ea))

- Fix for tarball creation
  ([`c8d6f7d`](https://github.com/quadsproject/badfish/commit/c8d6f7dedc38c5ded225ac22339524df6b9d66a4))

- Fixed tarball path
  ([`86f3223`](https://github.com/quadsproject/badfish/commit/86f322383e6b7c57e0071aa332318d529ccc0b63))

- Moved gha for create release to use gh cli
  ([`f06b354`](https://github.com/quadsproject/badfish/commit/f06b354114dda70bd3acfbf9b136449089678f5a))

### Documentation

- Adde to container volume mapping
  ([`029dad2`](https://github.com/quadsproject/badfish/commit/029dad28b24e17a1ff020e2e885bd76ef73880ba))

- Added badges plus --gif docs
  ([`9f3cd34`](https://github.com/quadsproject/badfish/commit/9f3cd34b41f5d23521c0dce61b1e02d7dc7dbe7a))

- Added CoC
  ([`c79c08c`](https://github.com/quadsproject/badfish/commit/c79c08c0ffc7736bd64a94449950962c0948f063))

- Added docs for boot-to-type
  ([`09ecddc`](https://github.com/quadsproject/badfish/commit/09ecddc9cbb9503222aaeb4e6899c1cf19a8f434))

fixes: https://github.com/redhat-performance/badfish/issues/23

- Added note for podman run to store files
  ([`c76c728`](https://github.com/quadsproject/badfish/commit/c76c728b2311d01ccfff0aea313e58bacf11f0bc))

- Added README instructions for RPM install
  ([`77d8967`](https://github.com/quadsproject/badfish/commit/77d8967197172b98272b1350e584f4427787052b))

Added instructions for RPM install plus usage as python library. Slight refactor of rpm.spec.tpl.
  Bumped version of pytest plus added python 3.10 environment to tox testing.

- Center BF image
  ([`0e4c969`](https://github.com/quadsproject/badfish/commit/0e4c9692b51690ef32679ccaf75369fcbd5fde81))

- Coc amendment
  ([`3ad65a8`](https://github.com/quadsproject/badfish/commit/3ad65a84f4016c562ccf4b540276bd4c958b7d54))

- New lines for bages
  ([`2f7aae0`](https://github.com/quadsproject/badfish/commit/2f7aae0d8a3d607a27a986c5a81924f055e26ac7))

- No new lines for badges
  ([`f5091ef`](https://github.com/quadsproject/badfish/commit/f5091ef83ce070b1d6978c71a4ee0f84b79a1a18))

- Removed support for virtualenv plus code example fixes
  ([`ca14c4a`](https://github.com/quadsproject/badfish/commit/ca14c4aff4ee739b4d1f249abe3e3dbf1c1b150b))

- Reworked virtualenv usage
  ([`7d57c46`](https://github.com/quadsproject/badfish/commit/7d57c4651683e7095c9fcae8cafda6351ab7d0aa))

- Updated contributing guide
  ([`2776c04`](https://github.com/quadsproject/badfish/commit/2776c04f3efd44b92acb32bbaee4aa626eb702be))

### Features

- Add ALIAS R750 override and minor doc.
  ([`9f6e4ff`](https://github.com/quadsproject/badfish/commit/9f6e4ff16fb3af07e095c31736f3cefb619f350d))

- Add GH CI for PR.
  ([`3b9498f`](https://github.com/quadsproject/badfish/commit/3b9498fe11f8c6abb26a978387fd4bdaa2e1b9f0))

* Add GHA for pull requests also.

- Add issue and push chat webhooks.
  ([`616626a`](https://github.com/quadsproject/badfish/commit/616626ad944c60f3d9c1c575f0ac34daecb58e8b))

* This adds GHA for accessing repo secrets to push chat notifications via webhooks for: - new issue
  creation - push events via https://github.com/marketplace/actions/workflow-webhook-action

- Added --gif
  ([`dcd1ad3`](https://github.com/quadsproject/badfish/commit/dcd1ad382aa65b26ebd1a6bacecd720977c2b9b6))

This generates a gif with all screenshots taken in a default period of 3 minutes with intervals of 5
  seconds. This can be modified by passing --minutes and --interval.

- Added --ls-jobs argparse.
  ([`9d976d4`](https://github.com/quadsproject/badfish/commit/9d976d4d40887b84a08bbd2affc2ccadbc7b420f))

Returns a list of active jobs if any or the following msg if none: "- INFO - No active jobs found."

- Added BIOS Setup password management plus check-job-status
  ([`1257d9c`](https://github.com/quadsproject/badfish/commit/1257d9c0262ff77d64e3a77f235636dde3049859))

closes: https://github.com/redhat-performance/badfish/issues/114

- Added boot-to-mac action
  ([`06d522a`](https://github.com/quadsproject/badfish/commit/06d522a2c7fc75af4849b9afe549e404cafe9601))

- Added Dockerfile for building development branch container
  ([`fe0efba`](https://github.com/quadsproject/badfish/commit/fe0efba0a86d35434c8142393f500d03a0c86916))

- Added force optional argument for clear-jobs
  ([`96eca22`](https://github.com/quadsproject/badfish/commit/96eca227a08fbb5796f96bce59c905cb84c09e09))

added log message for interface not being a valid boot device

- Added get and set for SRIOV global mode
  ([`ad725db`](https://github.com/quadsproject/badfish/commit/ad725dbc41ff0ff04598cf8f235b6da309339ff5))

- Added GH actions badge
  ([`76bdf32`](https://github.com/quadsproject/badfish/commit/76bdf3203999455272d1e2d210ac3073f2c398d0))

- Added github actions for rpm package build
  ([`0060ab1`](https://github.com/quadsproject/badfish/commit/0060ab18217aad1c207bfacb58ac59d12355e226))

This includes the rpm dir with a makefile and spec template. Ported over async_lru for lack of
  fedora packaging.

- Added handler for bad FQDN hostname
  ([`635b3a4`](https://github.com/quadsproject/badfish/commit/635b3a4515640efc712a3eddcdd2b9a00b9fbc7b))

- Added handler for unauthorized access
  ([`22657f9`](https://github.com/quadsproject/badfish/commit/22657f9b8e68f44b37db67cbe6788a7d605459ce))

- Added ls-interfaces
  ([`c730af7`](https://github.com/quadsproject/badfish/commit/c730af7cca746253c9e4b2f7a980aa23cdb849cd))

- Added ls-processors and ls-memory
  ([`6be2c29`](https://github.com/quadsproject/badfish/commit/6be2c299ca8f6361bf476200271b2ef0131925d0))

- Added new command for delta between firmware inventories
  ([`b40e3c3`](https://github.com/quadsproject/badfish/commit/b40e3c34b8e8be0ca9d0fc7528cf683763512625))

closes: https://github.com/redhat-performance/badfish/issues/302

- Added new command for listing server serial number
  ([`456f883`](https://github.com/quadsproject/badfish/commit/456f883bff5e56ef07e3a7a471ec0fb7bf8e3200))

style: code was styled with black and checked with flake8

closes: https://github.com/redhat-performance/badfish/issues/249

- Added pip upgrade to dockerfiles
  ([`3bacd6a`](https://github.com/quadsproject/badfish/commit/3bacd6ad9a0af8caff367fe2812a86baabb95b75))

- Added power control plus bios reset
  ([`3edbdbe`](https://github.com/quadsproject/badfish/commit/3edbdbe24159905b31c135e882e01516160865cf))

- Added PR template
  ([`357156a`](https://github.com/quadsproject/badfish/commit/357156afb809ea719d681cfbded8e6d89edcbb9e))

- Added reboot on boot change
  ([`05fe01f`](https://github.com/quadsproject/badfish/commit/05fe01f1c2c4fda9290280065cfbf4584c86c5f7))

closes:https://github.com/redhat-performance/quads/issues/309

- Added screenshot capabilities
  ([`5d13d80`](https://github.com/quadsproject/badfish/commit/5d13d80acf26a676c5e96454cec7b76268f99d44))

- Added set and get for bios attributes free-form
  ([`3dfd465`](https://github.com/quadsproject/badfish/commit/3dfd465f0eead4fe896a2f73a8c74134ef64dcb5))

- Added short FQDN to screenshot out
  ([`9bc6fa6`](https://github.com/quadsproject/badfish/commit/9bc6fa6d7db5210db9e549127eeb03430ee03c59))

- Added support for formatted output and ordered output for bulk actions
  ([`fa9daaf`](https://github.com/quadsproject/badfish/commit/fa9daaf72406cfb9432e39675093101f231889a9))

closes: https://github.com/redhat-performance/badfish/issues/250

closes: https://github.com/redhat-performance/badfish/issues/306

- Added support for UEFI boot mode on change/check boot order
  ([`9183078`](https://github.com/quadsproject/badfish/commit/918307857bb801af9302473e3d36f3e093821f51))

Additionally refactored exception handling and logging

closes: https://github.com/redhat-performance/badfish/issues/128

- Added test for boot-to-bad-mac
  ([`55302b5`](https://github.com/quadsproject/badfish/commit/55302b577ab34914f113aa0fb29b559b5bdafebe))

- Added tests for boot-to-mac and boot-to-type
  ([`c92cd77`](https://github.com/quadsproject/badfish/commit/c92cd777540c27b0a5b4b273405e42a5108fdd64))

- Added toggle for enabling/disabling boot device
  ([`0df57c5`](https://github.com/quadsproject/badfish/commit/0df57c54b4cd14a273bd71dda1278d1ff51f7cca))

- Added uefi boot source override
  ([`2b95af3`](https://github.com/quadsproject/badfish/commit/2b95af3ecd68c87655abdc9666a4b43774be4c81))

- Added VirtualMedia check and unmount
  ([`0cf31e7`](https://github.com/quadsproject/badfish/commit/0cf31e737d44dbe9386525f3b27a801e1b08d80a))

NOTE: All hosts can list the virtual media but unmount functionality

is only available for SuperMicro

- Change of authentification to tokeninzed
  ([`0c98cc2`](https://github.com/quadsproject/badfish/commit/0c98cc28061ca5e31bb49b65cc642ff042676e7c))

Closes: https://github.com/redhat-performance/badfish/issues/244

- Export and import SCP
  ([`fa1a038`](https://github.com/quadsproject/badfish/commit/fa1a038847c6849aefd1fc05e3097bba27069c67))

- Host type overrides
  ([`7d3b019`](https://github.com/quadsproject/badfish/commit/7d3b019b58c83a5ba79b3ffb9e149d89dd2b15a5))

- Make tox/lint run on PR's too.
  ([`37bfee3`](https://github.com/quadsproject/badfish/commit/37bfee34f872c198d24d030bd75246ee1bdd9bed))

* Run GHA CI for PR's too * Use `pull_request` instead of `pull_request_target` as tox and lint
  shouldn't need access to repo secrets.

reference: https://securitylab.github.com/research/github-actions-preventing-pwn-requests/

- Moved setup static meta to setup.cfg
  ([`fe15c94`](https://github.com/quadsproject/badfish/commit/fe15c94d443fc064ffc63859a924fa5313672788))

bumped version to 1.0.2 amended docs with new install method added pytest.ini and pyproject.toml

- Porting over quads changes w/asyncio
  ([`2be25ca`](https://github.com/quadsproject/badfish/commit/2be25ca45b4e16593b09b45fbd985f927d2152aa))

- Provide more accurate return codes
  ([`776bf01`](https://github.com/quadsproject/badfish/commit/776bf01fab7d182252b347dd062d2f41e86c553f))

- Removed hardcoded boot types
  ([`8054223`](https://github.com/quadsproject/badfish/commit/80542237abddbaf5068981f4d920b2972a889d0a))

we are now able to define on the interfaces yaml a free form type as the first string parsed from
  the key value when splitting it by _. We will parse the different types allowed from the yaml and
  display the available options if the type passed as argument doesn't match any of those.

- Replacing travis with GH actions
  ([`c505d71`](https://github.com/quadsproject/badfish/commit/c505d71e2aea420493a2030dea08007b0e10d0de))

- Rewrite and extension of features for virtual media
  ([`0b029a2`](https://github.com/quadsproject/badfish/commit/0b029a2d62f786503ad05e15a294f52032d3f0bf))

part of: https://github.com/redhat-performance/badfish/issues/228

- Sriov mode change check
  ([`9ebe6f9`](https://github.com/quadsproject/badfish/commit/9ebe6f93c60a7f3a979a2afde20ec19a16b0d1fd))

- Supermicro BMC reset
  ([`e985f9d`](https://github.com/quadsproject/badfish/commit/e985f9daac1b657f52a93c483af4401e80ce6d95))

closes: https://github.com/redhat-performance/badfish/issues/329

- Support for remote virtual media on nfs
  ([`96ab059`](https://github.com/quadsproject/badfish/commit/96ab0599a13f430855ff97eccbf174449b732207))

closes: https://github.com/redhat-performance/badfish/issues/228

### Testing

- Added gif tests
  ([`ec42b68`](https://github.com/quadsproject/badfish/commit/ec42b68e4f34bb68e862755764b094253dea6a60))

- Added job-queue and reset-bios plus refactoring
  ([`d434f95`](https://github.com/quadsproject/badfish/commit/d434f958b88866035f84a743d8759d08a5bd13ce))

- Added ls-interfaces
  ([`ad0ee09`](https://github.com/quadsproject/badfish/commit/ad0ee09afd87ae18d36ce6fb301f9a2659fa804a))

- Added tests for boot to uefi
  ([`ef3a26a`](https://github.com/quadsproject/badfish/commit/ef3a26a0f8494ad9702d7702faec3d7e9c4b2c49))

- Added tests for fw-inventory, ls-memory and ls-proc
  ([`641dee8`](https://github.com/quadsproject/badfish/commit/641dee8e808f37a5d9956dfa3c2aa37dff71b440))

- Added tests for virtual media check and unmount
  ([`ef2ebf8`](https://github.com/quadsproject/badfish/commit/ef2ebf88d5e2b1f2372a25ad8902b9c4ae9ab7db))

- Coveragerc to use src directory
  ([`576abc7`](https://github.com/quadsproject/badfish/commit/576abc713e5bfdd17092617cf8f736d231b2bb26))

- Fixes to custom_interfaces and boot_to
  ([`9e783a7`](https://github.com/quadsproject/badfish/commit/9e783a77fba08fa2f634e3447a6eae401bce6df4))

- Increased code coverage for badfish.py
  ([`a654394`](https://github.com/quadsproject/badfish/commit/a654394f1f7a6cc76dcdc64216661f72ee3b63bd))

- Increased code coverage for badfish.py
  ([`109be50`](https://github.com/quadsproject/badfish/commit/109be50d34d69de55b0a80064455061945487740))

- Removed 3.11 from GHA as asynctest not compatible
  ([`603a822`](https://github.com/quadsproject/badfish/commit/603a822bd104f66a22736897d109e5773607a270))
