import logging
import subprocess
import traceback
from subprocess import PIPE
from threading import Thread, Lock
from queue import Queue, Empty
import json

from core.libs.web.reporter import ReporterInstance


class Powershell():
    def __init__(self):
        self._stdout_queue = Queue()
        self._stdout_read_tread = None
        self._process = None
        self.lock = Lock()
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self, command, as_data = False, may_fail = False):
        self.lock.acquire()
        result = b""
        try:
            if as_data is True:
                if not command.endswith("ConvertTo-Json"):
                    command += " | ConvertTo-Json"
            result = self._execute_locked(command)
            if as_data is True:
                result = json.loads(result)
            return result
        except Exception as e:
            if may_fail is False:
                try:
                    result = result.decode("UTF-8")
                except:
                    pass
                try:
                    result = json.dumps(result)
                except:
                    result = None
                ReporterInstance.report("powershell_failed", {
                    "command" : command,
                    "exception": traceback.format_exc(),
                    "result": result
                })
                self._logger.debug("Failed to run powershell '%s' Exception: %s" % (command, e) )
            return None
        finally:
            self.lock.release()

    def _execute_locked(self, command):
        command = command.encode("UTF-8")
        if self._process is None:
            self._process = subprocess.Popen(['powershell'], stdin=PIPE, stderr=PIPE, stdout=PIPE)
        if self._stdout_read_tread is None:
            self._stdout_read_tread = Thread(target=self._read_thread, args=(self._process.stdout, self._stdout_queue), daemon=True)
            self._stdout_read_tread.start()
            self._stderr_read_tread = Thread(target=self._read_thread, args=(self._process.stderr, self._stdout_queue), daemon=True)
            self._stderr_read_tread.start()
        self._process.stdin.write(b'[Console]::OutputEncoding = [Text.Encoding]::UTF8 ; ')
        self._process.stdin.write(b'Write-Host __STARTMARKER__ ; ')
        self._process.stdin.write(b'' + command + b" ; ")
        self._process.stdin.write(b'Write-Host __ENDMARKER__ \n')
        self._process.stdin.flush()

        # FIXME : Sometimes causes an error if powershell decides to not respond?
        # FIXME2: Really?

        lines = []
        startfound = False
        while True:
            try:
                line = self._stdout_queue.get(timeout=12)
            except Empty:
                break
            if line == b"__ENDMARKER__\n":
                break
            if startfound == True:
                if line.startswith(b"PS "):  # may be powershell echo output
                    if line.endswith(command + b"\n"): continue  # skip command echoed by powershell
                    if line.endswith(b'Write-Host __STARTMARKER__\n'): continue  # skip startmarker
                    if line.endswith(b'Write-Host __ENDMARKER__\n'): continue  # skip endmarker
                lines.append(line)
            if line == b"__STARTMARKER__\n":
                startfound = True
        return b"".join(lines)

    def _read_thread(self, pipe, queue):
        for line in iter(pipe.readline, b''):
            line = line
            queue.put(line)
        pipe.close()
        self._stdout_read_tread = None




if __name__ == "__main__":
    ps = Powershell()
    #s = ps.execute("Get-NetFirewallProfile | ConvertTo-Json")
    s = ps.execute("C:\Windows\SysNative\pnputil.exe /enum-drivers /class Net")
    print(s)