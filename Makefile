# Python 2.7 only. nose under Python 3.12+ fails (`imp` removed).
# One-time setup:
#   CFLAGS="-std=c17" pyenv install 2.7.18
#   pyenv virtualenv 2.7.18 mtf-env
#   pyenv local mtf-env
#   make init

PY        ?= $(shell pyenv which python2 2>/dev/null || command -v python2)
PYTHONPATH_ := .:plmn
SUDO      ?= sudo env PATH="$$PATH" PYTHONPATH="$(PYTHONPATH_)" HOME="$$HOME"

init:
	$(PY) -m pip install -r requirements.txt nose

test:
	$(SUDO) $(PY) -m nose -v --match='(?:(?:^|[\b_\.-])[Tt]est|check)' tests

test-modem:
	$(SUDO) $(PY) tests/modem_checks.py --debug

test-sim:
	$(SUDO) $(PY) tests/sim_checks.py --debug

test-at:
	$(SUDO) $(PY) tests/at_checks.py --debug

test-simple:
	$(SUDO) $(PY) tests/simple_cmd_checks.py --debug

test-regression:
	$(SUDO) $(PY) tests/test_regression.py --debug

.PHONY: init test test-modem test-sim test-at test-simple test-regression
