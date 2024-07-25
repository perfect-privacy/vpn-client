import logging
import subprocess
import traceback
import uuid
import os
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
                command += " | ConvertTo-Json "
            result = self._execute_locked(command)
            if as_data is True:
                result = json.loads(result)
            return result
        except Exception as e:
            if may_fail is False:
                try:
                    result = result.decode("UTF-8", errors="replace")
                except:
                    pass
                if "A system shutdown is in progress" in result:
                    return None
                if "Der Computer wird" in result and "heruntergefahren" in result:
                    return None

                try:
                    result = json.dumps(result)
                except:
                    result = None
                ReporterInstance.report("powershell_failed", {
                    "command" : command,
                    "exception": traceback.format_exc(),
                    "result": result
                })
                self._logger.debug("Failed '%s' Exception: %s" % (command, e) )
            return None
        finally:
            self.lock.release()

    def _execute_locked(self, command):
        command = command.encode("UTF-8")
        uniq_id = ("%s" % uuid.uuid4()).split("-")[0].strip().encode("UTF-8")
        if self._process is None:
            self._process = subprocess.Popen([os.path.join(os.environ['SystemRoot'], 'System32', "WindowsPowerShell", "v1.0", "powershell.exe")], stdin=PIPE, stderr=PIPE, stdout=PIPE)
        if self._stdout_read_tread is None:
            self._stdout_read_tread = Thread(target=self._read_thread, args=(self._process.stdout, self._stdout_queue), daemon=True)
            self._stdout_read_tread.start()
            self._stderr_read_tread = Thread(target=self._read_thread, args=(self._process.stderr, self._stdout_queue), daemon=True)
            self._stderr_read_tread.start()
            self._process.stdin.write(b'[Console]::OutputEncoding = [Text.Encoding]::UTF8 ; ')
            self._process.stdin.write(b"$PSDefaultParameterValues['*:Encoding'] = 'utf8' ; ")
            self._process.stdin.write(b"Import-Module DnsClient ; ")
            self._process.stdin.write(b"Import-Module NetTCPIP ; ")
            self._process.stdin.write(b"Import-Module NetSecurity ; ")

        self._process.stdin.write(b'Write-Host __STARTMARKER-%s__ ; ' % uniq_id)
        self._process.stdin.write(b'' + command + b" ; ")
        self._process.stdin.write(b'Write-Host __ENDMARKER-%s__ \n' % uniq_id)
        try:
            self._process.stdin.flush()
        except:
            pass
        lines = []
        startfound = False
        while True:
            try:
                line = self._stdout_queue.get(timeout=60)
            except Empty:
                self._logger.debug("Timeout in '%s'" % command)
                break
            if line == b"__ENDMARKER-%s__\n" % uniq_id:
                break
            if startfound == True:
                if line.startswith(b"PS "):  # may be powershell echo output
                    if line.endswith(command + b"\n"): continue  # skip command echoed by powershell
                    if line.endswith(b'Write-Host __STARTMARKER-%s__\n' % uniq_id): continue  # skip startmarker
                    if line.endswith(b'Write-Host __ENDMARKER-%s__\n' % uniq_id): continue  # skip endmarker
                lines.append(line)
            if line == b"__STARTMARKER-%s__\n" % uniq_id:
                startfound = True
        return b"".join(lines)

    def _read_thread(self, pipe, queue):
        try:
            for line in iter(pipe.readline, b''):
                line = line
                queue.put(line)
            pipe.close()
        except:
            pass
        self._logger.debug("Read thread exited")
        if self._process is not None:
            self._process.kill()
        self._process = None
        self._stdout_read_tread = None

powershellInstance = None

def getPowershellInstance():
    global powershellInstance
    if powershellInstance is None:
        powershellInstance = Powershell()
    return powershellInstance
