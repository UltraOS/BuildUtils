import subprocess
import sys
import os
import __main__
import platform


def relaunch_in_wsl_if_windows():
    if platform.system() != "Windows":
        return

    path_to_script = __main__.__file__
    this_script = os.path.basename(path_to_script)

    ret = subprocess.run(["wsl", "python3", this_script, *sys.argv[1:]],
                         cwd=os.path.dirname(path_to_script))
    exit(ret.returncode)
