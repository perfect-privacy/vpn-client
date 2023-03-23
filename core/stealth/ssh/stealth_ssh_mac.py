# coding=utf-8

import os
import sys
import logging
import tempfile
import subprocess
import traceback
from gettext import gettext as _
from threading import Thread, Event, RLock

from config.files import SSH
from .stealth_ssh_common import SSHTunnel, StealthSSHCommon
from .stealth_ssh_common import SSHTunnelError

class StealthSSHMacos(StealthSSHCommon):
    def __init__(self, core, servergroup, openvpn_remote_ip, openvpn_remote_port):
        super().__init__(core, servergroup, openvpn_remote_ip, openvpn_remote_port)

        self.openssh_path = "/usr/bin/ssh"
        self.connect_timeout = 60

        self.on_interrupt_callback = None

        self._known_hosts_file = None
        self._config_file = None
        self._identity_file = None
        self._password_file = None
        self._askpass_file = None
        self._files_to_delete = []

        self._ssh_thread = None

        self._has_been_started = False
        self._connect_lock = RLock()
        self._stop_process_lock = RLock()
        self._stop_request = Event()

        self._interrupt_start_blocking_event = Event()
        self._connection_established = False
        self._connect_error = None

    def _compose_ssh_args(self):
        args = [
            self.openssh_path,
            "-oBatchMode=no",
            "-oKbdInteractiveAuthentication=no",
            "-oCheckHostIP=yes",
            "-oHashKnownHosts=no",
            "-oStrictHostKeyChecking=yes",
            # read ours instead of user's or global known_hosts file
            "-oUserKnownHostsFile=\"{}\"".format(self._known_hosts_file),
            "-oGlobalKnownHostsFile=\"{}\"".format(self._known_hosts_file),
            "-oNumberOfPasswordPrompts=1",
            "-oConnectTimeout={}".format(self.connect_timeout),
            # send keepalive if there's no traffic for longer than 5 seconds
            "-oServerAliveInterval=5",
            "-oServerAliveCountMax=6",  # max 30s
            "-oProtocol=2",
            # enforce ECDSA host key algorithm
            ("-oHostKeyAlgorithms="
             "ecdsa-sha2-nistp256-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp384-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp521-cert-v01@openssh.com,"
             "ssh-ed25519-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp256,"
             "ecdsa-sha2-nistp384,"
             "ecdsa-sha2-nistp521,"
             "ssh-ed25519"),
            #  don't read any other config file
            "-F", self._config_file,  # per-user configuration file (~/.ssh/config)
            "-oIdentityFile=\"{}\"".format(self._identity_file),  # per-user identiy file (~/.ssh/id_ecdsa)
            "-oIdentitiesOnly=yes",
            "-oPreferredAuthentications=password",
            "-oPubkeyAuthentication=no",
            "-oPasswordAuthentication=yes",
            "-v",  # verbose mode for "Auth succeeded" message
            "-N",  # don't execute a remote command
            "-x",  # disable X11 forwarding
            "-a",  # disable authentication agent connection forwarding
            "-T",  # disable pseudo-tty allocation
            "-l", self._ssh_username,
            "-p", str(self._ssh_port),
            "-L",
            "%s:%s:%s" % (self._ssh_local_port, self._openvpn_remote_ip, self._openvpn_remote_port),
            self._ssh_host
        ]
        return args

    def start(self):
        with self._connect_lock:
            if self._has_been_started:
                raise SSHTunnelError("unable to start the connection twice")

            self._logger.debug("starting")
            self._has_been_started = True

            # create temporary known_hosts file
            try:
                f, self._known_hosts_file = tempfile.mkstemp(prefix="ssh_known_hosts_", text=True)
                self._files_to_delete.append(self._known_hosts_file)
                with os.fdopen(f, "w") as f:
                    if self._ssh_port == 22:
                        # for default port 22 the square brackets and the port must be omitted
                        # otherwise the host verification will fail
                        f.write("{ip} {key}\n".format(ip=self._ssh_host, key=self._ssh_fingerprint))
                    else:
                        f.write("[{ip}]:{port} {key}\n".format(ip=self._ssh_host, port=self._ssh_port, key=self._ssh_fingerprint))
                os.chmod(self._known_hosts_file, 0o644)

                f, self._config_file = tempfile.mkstemp(prefix="ssh_config_", text=True)
                self._files_to_delete.append(self._config_file)
                with os.fdopen(f, "w") as f:
                    f.write("")
                os.chmod(self._config_file, 0o600)

                f, self._identity_file = tempfile.mkstemp(prefix="ssh_identity_", text=True )
                self._files_to_delete.append(self._identity_file)
                with os.fdopen(f, "w") as f:
                    f.write("")
                os.chmod(self._identity_file, 0o600)

                f, self._password_file = tempfile.mkstemp(prefix="ssh_pass_", text=True)
                self._files_to_delete.append(self._password_file)
                with os.fdopen(f, "w") as f:
                    f.write("")
                    f.flush()
                    os.chmod(self._password_file, 0o600)
                    f.write(self._ssh_password)

                # to prevent privilege escalation exploits,
                # don't echo the password directly but cat another file instead
                f, self._askpass_file = tempfile.mkstemp(prefix="ssh_askpass_", text=True)
                self._files_to_delete.append(self._askpass_file)
                with os.fdopen(f, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write("cat \"{pass_file}\"\n".format(pass_file=self._password_file))
                    f.write("exit 0\n")
                os.chmod(self._askpass_file, 0o700)

                self._logger.debug("created files: {}".format(self._files_to_delete))
            except Exception as e:
                self._logger.info("creating temporary files failed")
                raise SSHTunnelError(_("Creating temporary files failed"))

            # start ssh process
            self._ssh_thread = Thread(target=self._ssh_thread_run_method, daemon=True)
            self._interrupt_start_blocking_event.clear()
            self._ssh_thread.start()
            process_started = self._interrupt_start_blocking_event.wait(timeout=self.connect_timeout)
            if not process_started:
                raise SSHTunnelError("Timeout after {} seconds".format(self.connect_timeout))
            if not self._connection_established:
                raise self._connect_error if self._connect_error else SSHTunnelError("unable to establish connection")

    def _get_line_from_ssh_process(self):
        buff = ""
        done = False
        try:
            buff = self._ssh_process.stdout.read(8)
            self._ssh_process.stdout.flush()
        except Exception as e:
            done = True

        while not done or buff:
            if "\n" in buff:
                (line, buff) = buff.split("\n", 1)
                yield line + "\n"
            else:
                more = None
                try:
                    more = self._ssh_process.stdout.read(8)
                    self._ssh_process.stdout.flush()
                except Exception as e:
                    done = True

                if not more:
                    done = True
                else:
                    buff = buff + more

        if buff:
            yield buff

    def _ssh_thread_run_method(self):
        self._connection_established = False

        args = self._compose_ssh_args()
        self._logger.debug("executing '{}'".format(" ".join(args)))

        env = os.environ.copy()
        env["SSH_ASKPASS"] = self._askpass_file
        env["DISPLAY"] = "0"
        self._ssh_process = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, universal_newlines=True, start_new_session=True, bufsize=0)

        self._logger.info("Started SSH process with PID {}".format(self._ssh_process.pid))

        try:
            for line in self._get_line_from_ssh_process():
                line = line.strip()
                self._logger.debug("SSH[{}]: {}".format(self._ssh_process.pid, line))
                self._process_line(line)
        except SSHTunnelError as e:
            self._logger.error(e)
            self._connect_error = e
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_exception(exc_type, exc_value,
                                            exc_traceback, limit=2)
            self._logger.error(tb)

        self._logger.debug("no more lines left")
        self._interrupt_start_blocking_event.set()

        if not self._stop_request.is_set() and self._connection_established:
            try:
                self.on_interrupt_callback()
            except TypeError:
                pass
            except:
                self._logger.debug(traceback.format_exc())

        self._logger.debug("thread stopping")

        self._stop_process()

        while self._files_to_delete:
            f = self._files_to_delete.pop()
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
            except:
                self._logger.warning("removing temporary file at '{}' failed".format(self._known_hosts_file))

        self._logger.debug("thread stopped")

    def _process_line(self, line):
        if not self._connection_established:
            if "Could not resolve hostname" in line:
                raise SSHTunnelError("Could not resolve hostname")
            elif "Connection refused" in line:
                raise SSHTunnelError("Connection refused")
            elif "Network is unreachable" in line:
                raise SSHTunnelError("Network is unreachable")
            elif "Permission denied" in line:
                raise SSHTunnelError(msg="Permission denied", permission_denied=True)
            elif "Authentication failed" in line:
                self._logger.error("Authentication failed")
                raise SSHTunnelError("Authentication failed")
            elif "Connection closed by" in line:
                self._logger.error("Connection closed")
                raise SSHTunnelError("Connection closed")
            elif "Authentication succeeded" in line:
                self._logger.info("Authentication succeeded")
                self._logger.info("Waiting for server response")
            elif "Address already in use" in line:
                self._logger.error("Address already in use")
                raise SSHTunnelError("Port is already in use")
            elif "Connection timed out" in line:
                self._logger.error("Connection timed out")
                raise SSHTunnelError("Connection timed out")
            elif "Entering interactive session" in line:
                self._logger.info("SSH connection established")
                self._connection_established = True
                self._interrupt_start_blocking_event.set()

    def stop(self):
        with self._connect_lock:
            if not self._has_been_started:
                return

            self._logger.debug("stopping")

            self._stop_request.set()
            self._stop_process()

            if self._ssh_thread:
                self._ssh_thread.join(timeout=10)
                if self._ssh_thread.is_alive():
                    self._logger.error("terminating SSH thread failed")
                    return
            self._logger.debug("stopped")

    def _stop_process(self):
        if self._ssh_process.poll() is not None:
            return

        with self._stop_process_lock:

            self._ssh_process.terminate()
            self._ssh_process.wait(timeout=10)

            returncode = self._ssh_process.poll()
            if returncode is None:
                self._logger.warning("terminating SSH process failed. sending SIGKILL")
                self._ssh_process.kill()
                self._ssh_process.wait(timeout=2)
                returncode = self._ssh_process.poll()
                if returncode is None:
                    self._logger.error("killing SSH process failed. PID {} still running".format(self._ssh_process.pid))
            if returncode is not None:
                self._logger.debug("SSH process exited with return code {}".format(returncode))

    @property
    def is_running(self):
        return self._has_been_started and self._ssh_thread is not None and self._ssh_thread.is_alive()
'''


class SSHTunnel_MacOs(SSHTunnel):


    def __init__(self, host, port, key, valid_ips, username, password, local_port,
                 enable_forwarding=False, forwarded_remote_host=None, forwarded_remote_tcp_port=None):
        """
        :param host: the host to connect to
        :type host: str

        :param port: the port to connect to
        :type port: int

        :param key: the key
        :type key: str

        :param valid_ips: a list of valid IP addresses, ignored if empty
        :type valid_ips: list[str]

        :param username: the SSH username
        :type username: str

        :param password: the SSH password
        :type password: str

        :param local_port: the local port forwarded/SOCKS service will be available on
        :type local_port: int

        :param enable_forwarding: whether to forward, create local SOCKS proxy otherwise
        :type enable_forwarding: bool

        :param forwarded_remote_host: the remote host to forward to (unused for SOCKS)
        :type forwarded_remote_host: str

        :param forwarded_remote_tcp_port: the remote port to forward to (unused for SOCKS)
        :type forwarded_remote_tcp_port: int
        """

        self._logger = logging.getLogger(self.__class__.__name__)

        self._host = None
        self._port = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key = key
        self.valid_ips = valid_ips
        self._local_port = None
        self.local_port = local_port
        self.forwarding_enabled = enable_forwarding
        self._forwarded_remote_host = None
        self.forwarded_remote_host = forwarded_remote_host
        self._forwarded_remote_tcp_port = None
        self.forwarded_remote_tcp_port = forwarded_remote_tcp_port

        self.openssh_path = "/usr/bin/ssh"
        self.connect_timeout = 60

        self.connection_state = self.CONNECTION_STATE_DISCONNECTED
        self._status_message = _("Disconnected")

        self.on_interrupt_callback = None

        self._known_hosts_file = None
        self._config_file = None
        self._identity_file = None
        self._password_file = None
        self._askpass_file = None
        self._files_to_delete = []

        self._ssh_thread = None

        self._has_been_started = False
        self._connect_lock = RLock()
        self._stop_process_lock = RLock()
        self._stop_request = Event()

        self._interrupt_start_blocking_event = Event()
        self._connection_established = False
        self._connect_error = None

    def _create_logger(self):
        return logging.getLogger("{} ({}:{})".format(self.__class__.__name__, self.host, self.port))

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = self._sanitize_host(value)
        self._logger = self._create_logger()

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = self._sanitize_port(value)
        self._logger = self._create_logger()

    @property
    def local_port(self):
        return self._local_port

    @local_port.setter
    def local_port(self, value):
        self._local_port = self._sanitize_port(value)

    @property
    def forwarded_remote_host(self):
        return self._forwarded_remote_host

    @forwarded_remote_host.setter
    def forwarded_remote_host(self, value):
        self._forwarded_remote_host = self._sanitize_host(value)

    @property
    def forwarded_remote_tcp_port(self):
        return self._forwarded_remote_tcp_port

    @forwarded_remote_tcp_port.setter
    def forwarded_remote_tcp_port(self, value):
        self._forwarded_remote_tcp_port = self._sanitize_port(value)

    def _sanitize_host(self, host):
        """
        :return: a sanitized version of host (lowercase characters, digits and . remaining)
        :rtype: str
        :raise: ValueError
        """
        input_host = host
        host = "".join(c.lower() for c in host if c.isalnum() or c == "." or c == "-")
        if host == "localhost":
            host = "127.0.0.1"
        if input_host != host:
            self._logger.info("host '%s' sanitized to '%s'", input_host, host)
        if not host:
            raise ValueError("not a host")
        return host

    def _sanitize_port(self, value):
        """
        :return: port as int
        :raise: ValueError
        """
        port = int(value)
        if not self.is_port(port):
            raise ValueError("not a port")
        return port

    @staticmethod
    def is_port(port):
        try:
            return 0 <= port <= 65535
        except TypeError:
            return False

    def _compose_ssh_args(self):
        args = [
            self.openssh_path,
            "-oBatchMode=no",
            "-oKbdInteractiveAuthentication=no",
            "-oCheckHostIP=yes",
            "-oHashKnownHosts=no",
            "-oStrictHostKeyChecking=yes",
            # read ours instead of user's or global known_hosts file
            "-oUserKnownHostsFile=\"{}\"".format(self._known_hosts_file),
            "-oGlobalKnownHostsFile=\"{}\"".format(self._known_hosts_file),
            "-oNumberOfPasswordPrompts=1",
            "-oConnectTimeout={}".format(self.connect_timeout),
            # send keepalive if there's no traffic for longer than 5 seconds
            "-oServerAliveInterval=5",
            "-oServerAliveCountMax=6",  # max 30s
            "-oProtocol=2",
            # enforce ECDSA host key algorithm
            ("-oHostKeyAlgorithms="
             "ecdsa-sha2-nistp256-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp384-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp521-cert-v01@openssh.com,"
             "ssh-ed25519-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp256,"
             "ecdsa-sha2-nistp384,"
             "ecdsa-sha2-nistp521,"
             "ssh-ed25519"),
            #  don't read any other config file
            "-F", self._config_file,  # per-user configuration file (~/.ssh/config)
            "-oIdentityFile=\"{}\"".format(self._identity_file),  # per-user identiy file (~/.ssh/id_ecdsa)
            "-oIdentitiesOnly=yes",
            "-oPreferredAuthentications=password",
            "-oPubkeyAuthentication=no",
            "-oPasswordAuthentication=yes",
            "-v",  # verbose mode for "Auth succeeded" message
            "-N",  # don't execute a remote command
            "-x",  # disable X11 forwarding
            "-a",  # disable authentication agent connection forwarding
            "-T",  # disable pseudo-tty allocation
            "-l", self.username,
            "-p", str(self.port)
        ]

        if self.forwarding_enabled:
            args.append("-L")
            args.append("{local_port}:{forwarded_host}:{forwarded_port}".format(
                local_port=self.local_port, forwarded_host=self.forwarded_remote_host,
                forwarded_port=self.forwarded_remote_tcp_port))
        else:
            # create local SOCKS Proxy instead
            args.append("-D")
            args.append(str(self.local_port))

        args.append(self.host)

        return args

    def start(self):
        with self._connect_lock:
            if self._has_been_started:
                raise SSHTunnelError("unable to start the connection twice")

            if not self.host or not self.port or not self.valid_ips or not self.local_port or not self.key:
                raise SSHTunnelError("host configuration incomplete")
            if not self.username or not self.password:
                raise SSHTunnelError("credentials not set")

            self._logger.debug("starting")
            self._has_been_started = True

            # create temporary known_hosts file
            try:
                f, self._known_hosts_file = tempfile.mkstemp(prefix="ssh_known_hosts_", text=True)
                self._files_to_delete.append(self._known_hosts_file)
                with os.fdopen(f, "w") as f:
                    if self.port == 22:
                        # for default port 22 the square brackets and the port must be omitted
                        # otherwise the host verification will fail
                        f.write("{ip} {key}\n".format(ip=self.host, key=self.key))
                    else:
                        f.write("[{ip}]:{port} {key}\n".format(ip=self.host, port=self.port, key=self.key))
                os.chmod(self._known_hosts_file, 0o644)

                f, self._config_file = tempfile.mkstemp(prefix="ssh_config_", text=True)
                self._files_to_delete.append(self._config_file)
                with os.fdopen(f, "w") as f:
                    f.write("")
                os.chmod(self._config_file, 0o600)

                f, self._identity_file = tempfile.mkstemp(prefix="ssh_identity_", text=True )
                self._files_to_delete.append(self._identity_file)
                with os.fdopen(f, "w") as f:
                    f.write("")
                os.chmod(self._identity_file, 0o600)

                f, self._password_file = tempfile.mkstemp(prefix="ssh_pass_", text=True)
                self._files_to_delete.append(self._password_file)
                with os.fdopen(f, "w") as f:
                    f.write("")
                    f.flush()
                    os.chmod(self._password_file, 0o600)
                    f.write(self.password)

                # to prevent privilege escalation exploits,
                # don't echo the password directly but cat another file instead
                f, self._askpass_file = tempfile.mkstemp(prefix="ssh_askpass_", text=True)
                self._files_to_delete.append(self._askpass_file)
                with os.fdopen(f, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write("cat \"{pass_file}\"\n".format(pass_file=self._password_file))
                    f.write("exit 0\n")
                os.chmod(self._askpass_file, 0o700)

                self._logger.debug("created files: {}".format(self._files_to_delete))
            except Exception as e:
                self._logger.info("creating temporary files failed")
                raise SSHTunnelError(_("Creating temporary files failed"))

            # start ssh process
            self._ssh_thread = Thread(target=self._ssh_thread_run_method, daemon=True)
            self._interrupt_start_blocking_event.clear()
            self._ssh_thread.start()
            process_started = self._interrupt_start_blocking_event.wait(timeout=self.connect_timeout)
            if not process_started:
                raise SSHTunnelError("Timeout after {} seconds".format(self.connect_timeout))
            if not self._connection_established:
                raise self._connect_error if self._connect_error else SSHTunnelError("unable to establish connection")

    def _get_line_from_ssh_process(self):
        buff = ""
        done = False
        try:
            buff = self._ssh_process.stdout.read(8)
            self._ssh_process.stdout.flush()
        except Exception as e:
            done = True

        while not done or buff:
            if "\n" in buff:
                (line, buff) = buff.split("\n", 1)
                yield line + "\n"
            else:
                more = None
                try:
                    more = self._ssh_process.stdout.read(8)
                    self._ssh_process.stdout.flush()
                except Exception as e:
                    done = True

                if not more:
                    done = True
                else:
                    buff = buff + more

        if buff:
            yield buff

    def _ssh_thread_run_method(self):
        self._connection_established = False

        args = self._compose_ssh_args()
        self._logger.debug("executing '{}'".format(" ".join(args)))

        env = os.environ.copy()
        env["SSH_ASKPASS"] = self._askpass_file
        env["DISPLAY"] = "0"
        self._ssh_process = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, universal_newlines=True, start_new_session=True, bufsize=0)

        self._logger.info("started SSH process with PID {}".format(self._ssh_process.pid))

        try:
            for line in self._get_line_from_ssh_process():
                line = line.strip()
                self._logger.debug("SSH[{}]: {}".format(self._ssh_process.pid, line))
                self._process_line(line)
        except SSHTunnelError as e:
            self._logger.error(e)
            self._connect_error = e
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_exception(exc_type, exc_value,
                                            exc_traceback, limit=2)
            self._logger.error(tb)

        self._logger.debug("no more lines left")
        self._interrupt_start_blocking_event.set()

        if not self._stop_request.is_set() and self._connection_established:
            try:
                self.on_interrupt_callback()
            except TypeError:
                pass
            except:
                self._logger.debug(traceback.format_exc())

        self._logger.debug("thread stopping")

        self._stop_process()

        while self._files_to_delete:
            f = self._files_to_delete.pop()
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
            except:
                self._logger.warning("removing temporary file at '{}' failed".format(self._known_hosts_file))

        self._logger.debug("thread stopped")

    def _process_line(self, line):
        if not self._connection_established:
            if "Could not resolve hostname" in line:
                raise SSHTunnelError("Could not resolve hostname")
            elif "Connection refused" in line:
                raise SSHTunnelError("Connection refused")
            elif "Network is unreachable" in line:
                raise SSHTunnelError("Network is unreachable")
            elif "Permission denied" in line:
                raise SSHTunnelError(msg="Permission denied", permission_denied=True)
            elif "Authentication failed" in line:
                self._logger.error("Authentication failed")
                raise SSHTunnelError("Authentication failed")
            elif "Connection closed by" in line:
                self._logger.error("Connection closed")
                raise SSHTunnelError("Connection closed")
            elif "Authentication succeeded" in line:
                self._logger.info("Authentication succeeded")
                self._logger.info("Waiting for server response")
            elif "Address already in use" in line:
                self._logger.error("Address already in use")
                raise SSHTunnelError("Port is already in use")
            elif "Connection timed out" in line:
                self._logger.error("Connection timed out")
                raise SSHTunnelError("Connection timed out")
            elif "Entering interactive session" in line:
                self._logger.info("SSH connection established")
                self._connection_established = True
                self._interrupt_start_blocking_event.set()

    def stop(self):
        with self._connect_lock:
            if not self._has_been_started:
                return

            self._logger.debug("stopping")

            self._stop_request.set()
            self._stop_process()

            if self._ssh_thread:
                self._ssh_thread.join(timeout=10)
                if self._ssh_thread.is_alive():
                    self._logger.error("terminating SSH thread failed")
                    return
            self._logger.debug("stopped")

    def _stop_process(self):
        if self._ssh_process.poll() is not None:
            return

        with self._stop_process_lock:

            self._ssh_process.terminate()
            self._ssh_process.wait(timeout=10)

            returncode = self._ssh_process.poll()
            if returncode is None:
                self._logger.warning("terminating SSH process failed. sending SIGKILL")
                self._ssh_process.kill()
                self._ssh_process.wait(timeout=2)
                returncode = self._ssh_process.poll()
                if returncode is None:
                    self._logger.error("killing SSH process failed. PID {} still running".format(self._ssh_process.pid))
            if returncode is not None:
                self._logger.debug("SSH process exited with return code {}".format(returncode))

    @property
    def is_running(self):
        return self._has_been_started and self._ssh_thread is not None and self._ssh_thread.is_alive()

'''