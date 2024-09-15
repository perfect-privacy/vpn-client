#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2014-2015 Perfect Privacy <support@perfect-privacy.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import os
import sys
import time
from signal import SIGTERM, SIGKILL
import errno
import argparse
import logging
import signal
from config.files import LOG_FILE
from config.config import FRONTEND
from core.core import Core
from core.libs.logger import Logger
from gui import getPyHtmlGuiInstance

class Daemon(object):
    def __init__(self, log_recorder):
        self.log_recorder = log_recorder
        self._logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        self.core = None
        signal.signal(signal.SIGTERM, self.on_sigterm)
        signal.signal(signal.SIGINT, self.on_sigint)

    def run(self):
        self.running = True
        self.core = Core(self.log_recorder)
        self.core.on_exited.attach_observer(self.on_core_exited)
        self.gui = getPyHtmlGuiInstance(
            frontend=FRONTEND,
            appInstance=self.core,
            on_frontend_ready=self.core.on_frontend_connected,
            on_frontend_exit=self.core.on_frontend_disconnected,
        )
        self.gui.start(show_frontend=False, block=False)

        while self.running:
            time.sleep(1)

        # shutdown
        self._logger.info("shutting down")
        self.core.quit()


    def on_core_exited(self, sender):
        self._logger.debug("core exited")
        self.running = False

    def on_sigterm(self, signal_number, interrupted_stack_frame):
        if not self.running:
            return
        self._logger.info("SIGTERM received")
        self.running = False

    def on_sigint(self, signal_number, interrupted_stack_frame):
        if not self.running:
            return
        self._logger.info("SIGINT received")
        self.running = False

class DaemonManager(object):

    def __init__(self, pidfile='pid.txt', stdin='/dev/null', stdout='/dev/null', stderr=None):

        self._logger = logging.getLogger(self.__class__.__name__)

        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        if not self.stderr:
            self.stderr = self.stdout

        # read PID from pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                self.pid = int(pf.read().strip())
        except (IOError, ValueError):
            self.pid = None

    def _cleanup(self):
        try:
            os.remove(self.pidfile)
        except FileNotFoundError:
            pass
        self.pid = None

    def start(self, args, **kwargs):
        self._logger.info("start")

        if self.pid:
            sys.stderr.write("Start aborted - PID file '{}' exists.\n".format(self.pidfile))
            sys.exit(1)

        if not args.no_daemon:
            # start as daemon (fork twice)
            self._daemonize()

        # execute main method, blocking
        daemon = Daemon(**kwargs)
        daemon.run()

        # remove pid file after main method exited
        self._cleanup()

    def stop(self, args, **kwargs):
        self._logger.info("stop")

        if not self.pid:
            sys.stderr.write("Could not stop, pid file '{}' missing.\n".format(self.pidfile))
            sys.exit(1)

        sigterm_sent = False
        try:
            sys.stdout.write("stopping")
            for i in range(30):
                sys.stdout.write("..")
                sys.stdout.flush()
                if i > 25:
                    os.kill(self.pid, SIGKILL)
                else:
                    os.kill(self.pid, SIGTERM)
                sigterm_sent = True
                time.sleep(.5)
                sys.stdout.write("..")
                sys.stdout.flush()
                time.sleep(.5)
        except OSError as err:
            if err.errno == errno.ESRCH:  # No such process
                old_pid = self.pid

                # remove pid file
                # ie. daemon killed by SIGKILL and couldn't delete it itself
                try:
                    os.remove(self.pidfile)
                except:
                    pass
                self.pid = None

                if sigterm_sent:
                    # the process existed and we killed it
                    sys.stdout.write(" ok.\n")
                else:
                    # the process didn't exist at all
                    sys.stdout.write(" Didn't do anything: There's no such process with PID {}.\n".format(old_pid))
            else:  # unknown error
                sys.stderr.write(" failed: {}\n".format(err))
                sys.exit(1)

    def restart(self, args, **kwargs):
        self._logger.info("restart")
        if self.pid:
            self.stop(args)
        self.start(args)

    def _daemonize(self):
        """
        Dadurch wird der aktuelle Prozess in einen Daemon umgewandelt.
        Die Argumente stdin, stdout und stderr sind Dateinamen, die
        wird geöffnet und als Ersatz für die Standard-Dateideskriptoren verwendet
        in sys.stdin, sys.stdout und sys.stderr.
        Diese Argumente sind optional und stehen standardmäßig auf /dev/null.
        Beachte, dass stderr ungepuffert geöffnet wird, also
        wenn es eine Datei mit stdout teilt, dann interleaved output
        erscheinen vielleicht nicht in der Reihenfolge, die du erwartest.
        """
        # Do first fork
        try:
            pid = os.fork()
            if pid > 0:
                time.sleep(.5)
                sys.exit(0)  # Exit first parent
        except OSError as e:
            sys.stderr.write("fork #1 failed: ({}) {}\n".format(e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir("/")
        os.umask(0)
        os.setsid()

        # Do second fork.
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Exit second parent
        except OSError as e:
            sys.stderr.write("fork #2 failed: ({}) {}\n".format(e.errno, e.strerror))
            sys.exit(1)

        # Open file descriptors and print start message
        with open(self.stdin, 'r') as si, open(self.stdout, 'a+') as so, \
                open(self.stderr, 'a+', buffering=1) as se:

            pid = str(os.getpid())
            sys.stdout.write("daemon started with PID {}\n".format(pid))
            try:
                sys.stdout.flush()
            except:
                pass
            if self.pidfile:
                with open(self.pidfile, 'w+') as pf:
                    os.chmod(self.pidfile, 0o644)
                    pf.write("{}\n".format(pid))

            # Redirect standard file descriptors
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())


def parse_arguments(start, stop, restart):
    parser = argparse.ArgumentParser()

    sp = parser.add_subparsers()
    sp_start = sp.add_parser('start', help='Startet den Daemon')
    sp_start.set_defaults(func=start)

    sp_stop = sp.add_parser('stop', help='Stoppt den Daemon')
    sp_stop.set_defaults(func=stop)

    sp_restart = sp.add_parser('restart', help='Startet den Daemon neu')
    sp_restart.set_defaults(func=restart)

    parser.add_argument("-v",  "--verbose",    action="count",      help="Ausführlichkeit der Ausgabe erhöhen", default=0)
    parser.add_argument("-q",  "--quiet",      action="store_true", help="keine Ausgabe ausgeben")
    parser.add_argument("-nd", "--no-daemon",  action="store_true", help="nicht als Hintergrundprozess laufen lassen")
    parser.add_argument("-nr", "--no-root",    action="store_true", help="als Nicht-Root laufen lassen")
    return parser.parse_args()

class LinuxDaemon():
    def __init__(self):
        self.logger = Logger(quiet=True)

    def from_commandline(self):
        PID_FILE = "/var/run/perfect-privacy-service.pid"
        daemonManager = DaemonManager(pidfile=PID_FILE, stdout=LOG_FILE)
        args = parse_arguments(daemonManager.start, daemonManager.stop, daemonManager.restart)

        if not args.no_root:
            if os.geteuid() != 0:
                sys.stderr.write("need to be root\n")
                sys.exit(1)

        # start/stop/restart
        try:
            args.func(args, log_recorder=self.logger)
        except AttributeError:
            # no command given -> start
            daemonManager.start(args, log_recorder=self.logger)
