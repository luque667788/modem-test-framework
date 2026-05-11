# PLMN Regression Project

Regression framework for checking modem status, registration, and connectivity via ModemManager/mmcli. Targets Quectel modems (EG25-G and compatible); standard 3GPP AT commands used throughout.

---

## Requirements

- Linux with ModemManager and mmcli installed
- Python **2.7** (see setup below — Python 3 is not supported)
- Root/sudo access (tests talk to ModemManager over dbus)
- A supported modem connected and recognized by ModemManager

---

## Setup

### 1. Install Python 2.7 via pyenv

Python 2.7 is EOL and its build requires an older C standard flag:

```bash
CFLAGS="-std=c17" pyenv install 2.7.18
```

### 2. Create and activate a virtualenv

```bash
pyenv virtualenv 2.7.18 mtf-env   # create the env
pyenv local mtf-env               # auto-activate in this directory
```

### 3. Install dependencies

```bash
make init
```

This runs `pip install -r requirements.txt nose` inside the virtualenv.

---

## Running Tests

All test commands must be run with `sudo` and with `PYTHONPATH` set so that the `plmn` modules resolve correctly. The Makefile handles both automatically.

### Run the full suite

```bash
make test
```

### Run individual suites

```bash
make test-modem     # modem presence, state, SIM checks
make test-sim       # SIM present, unlocked, registered
make test-at        # AT command checks (requires ModemManager in debug mode)
make test-simple    # mmcli simple-status / simple-connect
make test-regression
```

### Run a single file manually

If you need to run a file directly (e.g. for a one-off debug session):

```bash
sudo env PATH="$PATH" PYTHONPATH=".:plmn" python2 tests/modem_checks.py --debug
```

The `PATH` passthrough ensures pyenv's `python2` shim is found under sudo. The `PYTHONPATH` makes internal modules (`plmn/`) importable.

### Run a specific test method

```bash
sudo env PATH="$PATH" PYTHONPATH=".:plmn" \
  $(pyenv which python2) -m nose -v \
  tests/at_checks.py:AtCmdChecks.test_at_basic_cmds
```

---

## Manual-Only Tests

Some tests are decorated with `@unittest.skip` because they are destructive or time-consuming (3GPP network scan, manual network registration). To run them:

1. Open the relevant file (e.g. `tests/at_checks.py`)
2. Comment out the `@unittest.skip(...)` line above the test
3. Run the file or the specific method (see above)
4. Restore the decorator when done

Tests currently gated this way:

| Test | File | Reason |
|---|---|---|
| `test_at_3gpp_scan` | `at_checks.py` | Long scan, not safe for regression |
| `test_at_auto_register` | `at_checks.py` | Changes registration state |
| `test_at_manual_register` | `at_checks.py` | Changes registration state |

---

## ModemManager Debug Mode

AT commands via `mmcli --command` require ModemManager to be started with the `--debug` flag. The test suite handles this automatically: if debug mode is not active, it installs a systemd drop-in and restarts the daemon.

To check manually:

```bash
ps -ef | grep "ModemManager --debug"
```

To enable manually (persistent across reboots):

```bash
sudo mkdir -p /etc/systemd/system/ModemManager.service.d
sudo tee /etc/systemd/system/ModemManager.service.d/debug.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/usr/sbin/ModemManager --debug
EOF
sudo systemctl daemon-reload
sudo systemctl restart ModemManager
```

---

## Project Layout

### `plmn/`

| File | Purpose |
|---|---|
| `runner.py` | `Runner.run_cmd(cmd)` — subprocess wrapper, captures stdout/stderr |
| `results.py` | `Results` — singleton state store for test steps, errors, parsed values |
| `mmcli_parser.py` | Parses `mmcli -K` (keyvalue) output into nested dicts |
| `utils.py` | Logging setup, `--debug` argument parsing |
| `modem_cmds.py` | mmcli wrappers: list modem, check state, SIM checks, debug mode |
| `simple_cmds.py` | Wrappers for `mmcli --simple-status` / `--simple-connect` |
| `at_cmds.py` | AT command wrappers via `mmcli --command` |
| `network_checks.py` | Network registration and APN connect routines |

#### `mmcli_parser.py`

Uses `mmcli -K` (machine-readable keyvalue output) rather than human-formatted output. This avoids ANSI color codes and unstable column layout. Output like:

```
modem.generic.state : connected
modem.3gpp.registration-state : home
```

is parsed into a nested dict:

```python
{ "Status": { "state": "connected" }, "3GPP": { "registration": "home" } }
```

#### `at_cmds.py`

AT commands route through `mmcli -m N --command='AT...'` → ModemManager dbus → modem serial port. The framework never opens `/dev/ttyUSB*` directly. All commands use standard 3GPP `AT+` syntax (previously Sierra Wireless `AT!` vendor commands, not compatible with Quectel).

### `tests/`

| File | What it tests |
|---|---|
| `python_checks.py` | Python version sanity |
| `daemons_check.py` | ModemManager and NetworkManager running, wwan interface present |
| `modem_checks.py` | Modem listed, enabled, SIM present/unlocked/registered |
| `sim_checks.py` | SIM-specific checks |
| `at_checks.py` | AT command responses (basic commands + optional manual tests) |
| `simple_cmd_checks.py` | `mmcli --simple-status` fields |
| `test_regression.py` | Runs all suites as a single regression pass |
| `network_register_atnt.py` | End-to-end AT&T registration scenario |
| `network_register_verizon.py` | End-to-end Verizon registration scenario |
| `network_register_worldsim.py` | End-to-end WorldSim registration scenario |
| `compat.py` | Path fix so tests run from either `tests/` or repo root |
