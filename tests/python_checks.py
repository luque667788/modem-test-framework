import re
import unittest
import sys

import compat
from plmn.results import *
from plmn.runner import *

class PythonChecks(unittest.TestCase):
    def test_python_location(self):
        python_exec = Runner.run_cmd('which python').strip()

        if len(python_exec) is 0:
            Results.add_error('which python', 'Python not installed. Please install python using: sudo apt-get install python2.7')
        else:
            Results.add_state('Python Exec', python_exec)

    def test_python_version(self):
        python_ver = Runner.run_cmd('python --version')
        python_ver_major = re.findall(r'[0-9]+', python_ver)[0]
        python_ver_minor = re.findall(r'[0-9]+', python_ver)[1]
        # Suite is developed with Python 2.7+ in mind.
        if int(python_ver_major) != 2 or int(python_ver_minor) < 7:
            Results.add_error('Python 2.7+ version not present. Please install latest python 2.7 using: sudo apt-get install python2.7')
        else:
            Results.add_state('Python Version', python_ver.strip())
            Results.add_state('Python Major Version', python_ver_major.strip())
            Results.add_state('Python Minor Version', python_ver_minor.strip())


if __name__ == '__main__':
    nargs = process_args()
    unittest.main(argv=sys.argv[nargs:], exit=False)
    Results.print_results()

