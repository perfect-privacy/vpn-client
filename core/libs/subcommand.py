import os
import signal
import subprocess
import logging
import threading
from pyhtmlgui import Observable


class SubCommand():
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def run(self, cmd, args = [], timeout=60):
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
            msg = "%s , Success: %s" % ( args, success)
        except Exception as e:
            msg = "%s , Failed: %s" % ( args, e)

        if success is False or stderr != b"":
            if stdout != b"":
                msg += ", Stdout: %s " % ( stdout[:1000].strip())
            if stderr != b"":
                msg += ", Stderr: %s " % ( stderr[:1000].strip())
        self._logger.debug(msg)

        return success, stdout, stderr


class MySubProcess():
    def __init__(self,command, args = [], env={}):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.command = command
        self.args = args
        self.env = env

        self.on_output_event = Observable()
        self.on_exited_event = Observable()

        self._process = None
        self._pid = None
        self._output_data = []
        self._success = False
        self._lock = threading.Lock()

    def get_stderr(self):
        return b''.join([o[1] for o in self._output_data if o[0] == "e"])

    def get_stdout(self):
        return b''.join([o[1] for o in self._output_data if o[0] == "o"])

    def write_stdin(self, data):
        if self._process is not None:
            try:
                self._process.stdin.write(data)
            except Exception as e:
                self._logger.error("Failed to write to process")

    def start(self):
        if self._process is not None:
            raise Exception("Process already active")

        env = os.environ.copy()
        env.update(self.env)
        self._process = subprocess.Popen([self.command] + self.args, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
        try:
            self._pid = self._process.pid
        except Exception as e:
            self._logger.error("Failed to start process %s" % self.command)
            return

        self._stdout_read_tread = threading.Thread(target=self._read_stdout_thread, daemon=True)
        self._stderr_read_tread = threading.Thread(target=self._read_stderr_thread, daemon=True)
        self._stdout_read_tread.start()
        self._stderr_read_tread.start()

    def join(self, timeout = None):
        self._wait_exit(timeout)
        return [self._success, self.get_stdout(), self.get_stderr()]

    def stop(self, timeout = 10):
        if self._process is not None and self._process.poll() is None:
            try:
                self._process.terminate()
            except:
                pass
            self._wait_exit(timeout)
        if self._process is not None and self._process.poll() is None:
            self._logger.debug("Process not dead, killing")
            try:
                self._process.kill()
                os.kill(self._pid, signal.SIGKILL)
            except:
                pass
            self._wait_exit(timeout)

        if self.check_exited() is False:
            self._logger.error("Process did not die")

    def _wait_exit(self, timeout):
        try:
            self._process.wait(timeout)
        except:
            pass
        self.check_exited()

    def _read_stderr_thread(self):
        try:
            for data in iter(self._process.stderr.readline, b''):
                self.on_output_event.notify_observers(source="stderr", data=data)
                self._output_data.append(["e", data])
            self._process.stderr.close()
        except Exception as e:
            print(e)
        self._stderr_read_tread = None
        self.check_exited()

    def _read_stdout_thread(self):
        try:
            for data in iter(self._process.stdout.readline, b''):
                self.on_output_event.notify_observers(source="stdout", data=data)
                self._output_data.append(["o", data])
            self._process.stdout.close()
        except Exception as e:
            print(e)
            pass
        self._stdout_read_tread = None
        self.check_exited()

    def check_exited(self):
        with self._lock:
            if self._process is None:
                return True
            if self._process is not None and self._process.poll() is not None: # process has exited
                try:
                    self._stderr_read_tread.join(2)
                except:
                    pass
                try:
                    self._process.stderr.close()
                except:
                    pass
                try:
                    self._stdout_read_tread.join(2)
                except:
                    pass
                try:
                    self._process.stdout.close()
                except:
                    pass

            if self._process is not None and self._process.poll() is not None: # process has exited
                self._success = self._process.returncode == 0
                self._process = None
                self.on_exited_event.notify_observers(success=self._success)

            return self._process is None
