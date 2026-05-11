# -*- coding: utf-8 -*-

import compat
import unittest
import re
import sys

from plmn.utils import *
from plmn.results import *
from plmn.modem_cmds import ModemCmds
from plmn.runner import *
from plmn.at_cmds import *


class AtCmdChecks(unittest.TestCase):
    def setUp(self):
        AtCmds.modem_sanity()
        # Check if modemmanager is in debug mode or socat application is installed.

    def test_modem_mgr_debug_mode(self):
        AtCmds.mm_debug_mode()

    def test_at_unlock(self):
        AtCmds.unlock_at_cmds()

    def test_at_basic_cmds(self):
        AtCmds.mm_debug_mode()
        AtCmds.unlock_at_cmds()

        # Check AT command version
        res = AtCmds.send_at_cmd("AT&V")
        assert res is not None

        # Check for model number
        res = AtCmds.send_at_cmd("AT+GMM")
        assert res is not None

        # Check for manufacturer
        res = AtCmds.send_at_cmd("AT+GMI")
        assert res is not None

        # Check modem capabilities.
        res = AtCmds.send_at_cmd("AT+GCAP")
        assert res is not None

        # Check current registration (manual or automatic)
        res = AtCmds.send_at_cmd("AT+COPS?")
        assert res is not None

        # Check modem firmware version.
        res = AtCmds.send_at_cmd("AT+CGMR")
        assert res is not None

        # Ported from Sierra `AT!*` commands to Quectel / 3GPP equivalents.
        # Original Sierra commands kept in comments for reference.

        # Check supported radio access modes  (Sierra: AT!SELRAT=?)
        res = AtCmds.send_at_cmd('AT+QCFG="nwscanmode"')
        assert res is not None

        # Check PDP context activation state  (Sierra: AT!SCACT?)
        res = AtCmds.send_at_cmd("AT+CGACT?")
        assert res is not None

        # Check LTE serving cell info  (Sierra: AT!LTEINFO=?)
        res = AtCmds.send_at_cmd('AT+QENG="servingcell"')
        assert res is not None

        # Check network/registration info  (Sierra: AT!LTENAS?)
        res = AtCmds.send_at_cmd("AT+QNWINFO")
        assert res is not None

        # Antenna selection: no portable Quectel equivalent. Skip.
        # (Sierra: AT!ANTSEL=?)

        # Query supported + current bands  (Sierra: AT!BAND=? / AT!GETBAND?)
        res = AtCmds.send_at_cmd('AT+QCFG="band"')
        assert res is not None
        assert "No Service" not in res, 'AT Command QCFG="band" reporting no service'

        # Query signal/serving-cell status  (Sierra: AT!GSTATUS?)
        res = AtCmds.send_at_cmd("AT+QCSQ")
        assert res is not None

        # Query functional mode  (Sierra: AT^MODE? -- Huawei, never matched anyway)
        res = AtCmds.send_at_cmd("AT+CFUN?")
        assert res is not None

        # Query preferred PLMN list  (Sierra: AT!NVPLMN?)
        res = AtCmds.send_at_cmd("AT+CPOL?")
        assert res is not None

        # Check PS (Packet Service) attached  (Sierra: AT!SELMODE?)
        res = AtCmds.send_at_cmd("AT+CGATT?")
        assert res is not None
        assert "+CGATT: 1" in res, "PS domain not attached"

        # Query currently configured profile details.
        res = AtCmds.send_at_cmd("AT+CGDCONT?")
        assert res is not None

    # @unittest.skip("Skip 3GPP scanning. Enable this for manual run.")
    def test_at_3gpp_scan(self):
        AtCmds.perform_3gpp_scan()

    def test_at_auto_register(self):
        AtCmds.perform_auto_register()


if __name__ == "__main__":
    nargs = process_args()
    unittest.main(argv=sys.argv[nargs:], exit=False)
    Results.print_results()
