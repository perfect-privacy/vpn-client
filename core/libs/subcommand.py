import subprocess
import logging
import time

class SubCommand():
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def run(self, cmd, args = [], timeout=10):
        args = [cmd] + args
        success = False
        stdout = b""
        stderr = b""
        try:
            proc = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
            success = proc.returncode == 0
            msg = "Command: %s , Success: %s" % ( args, success)
        except Exception as e:
            msg = "Command: %s , Failed: %s" % ( args, e)

        if success is False or stderr != b"":
            if stdout != b"":
                msg += ", Stdout: %s " % ( stdout[:1000].strip())
            if stderr != b"":
                msg += ", Stderr: %s " % ( stderr[:1000].strip())
        self._logger.debug(msg)

        return success, stdout, stderr