import logging
import tempfile
import os
import subprocess
import traceback
from collections import namedtuple
from threading import RLock

from pyhtmlgui import Observable

from core.libs.web import reporter
from .leakprotection_generic import LeakProtection_Generic

TRANSPORT_PROTOCOL_UDP = "udp"
TRANSPORT_PROTOCOL_TCP = "tcp"

PFCTL = "/sbin/pfctl"

Hop = namedtuple("Hop", "hop_id public_ip_address port transport_protocol interface")
class LeakProtection_macos(LeakProtection_Generic):
    def __init__(self, core=None):
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)
        self.current_rules_str = None
        super().__init__(core=core)

    def _enable(self):
        self._logger.info("adjusting firewall")
        rules = [
            "set skip on lo0",
            "block in all",
            "block out all",
        ]
        if self._whitelisted_server is not None:
            public_ip_address, port, protocol = self._whitelisted_server
            rules.append("pass out  inet proto {protocol} to {public_ip_address} port {port} keep state".format( protocol=protocol, public_ip_address=public_ip_address, port=port))

        for hop in self.core.session.hops:
            if hop.connection is not None and hop.connection.openvpn_device is not None:
                rules.append("pass out on %s all keep state" % hop.connection.openvpn_device)

        rules.extend([
            "pass out inet to 10.0.0.0/8".format(),
            "pass in  inet from 10.0.0.0/8".format(),
            "pass out inet to 192.168.0.0/16".format(),
            "pass in  inet from 192.168.0.0/16".format(),
            "pass out inet to 172.16.0.0/12".format(),
            "pass in  inet from 172.16.0.0/12".format(),
            "pass out inet proto UDP to 224.0.0.251 port 5353".format(),  # mDNS / local discovery
            "pass out inet to 169.254.0.0/16".format(),  # link-local (works on primary interface only)
        ])

        rules_str = "\n".join(rules) + "\n"
        if rules_str != self.current_rules_str:
            self._logger.debug("Updating firewall rules")
            self.current_rules_str = rules_str
            try:
                fd, path = tempfile.mkstemp(prefix="pf_")
                with os.fdopen(fd, "w") as f:
                    f.write(rules_str)

                subprocess.Popen([PFCTL, "-f", path]).communicate()
                subprocess.Popen([PFCTL, "-e"]).communicate()
                subprocess.Popen([PFCTL, "-F", "states"]).communicate()

            except Exception as e:
                self._logger.error("unexpected exception: {}".format(e))
                self._logger.debug(traceback.format_exc())
                reporter.report_error(traceback=traceback.format_exc())


    def _disable(self):
        if self.current_rules_str != "":
            self._logger.info("turning off firewall")
            subprocess.Popen([PFCTL, "-d"]).communicate()
            self.current_rules_str = ""













class MacOsFirewall(LeakProtection_Generic):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._enabled = False
        self._primary_interface = ""
        self._hops = []
        self.number_of_hops_in_current_cascading = 0
        self._is_blocking_all_internet_traffic = False
        self.on_change = Observable()
        self._enable_disable_lock = RLock()

    def _log_current_config(self):
        self._logger.debug("current config: enabled: {}, primary interface: {}, hops: {}".format(
            self._enabled, self.primary_interface, self._hops))

    @property
    def primary_interface(self):
        return self._primary_interface

    @primary_interface.setter
    def primary_interface(self, value):
        self._primary_interface = value
        self._log_current_config()

    @property
    def is_blocking_all_internet_traffic(self):
        return self._is_blocking_all_internet_traffic

    def add_hop(self, public_ip_address, port, transport_protocol, interface=None):
        self._hops.append(Hop(len(self._hops) + 1, public_ip_address, port, transport_protocol, interface))
        self._log_current_config()

    def modify_hop(self, hopid, interface):
        self._logger.debug("modify hop {} to interface {}".format(hopid, interface))
        if hopid-1 < 0 or hopid-1 >= len(self._hops):
            self._logger.error("unknown hopid {}".format(hopid))
            reporter.report_error(msg="unknown hopid {}".format(hopid))
            return
        mod_hop = self._hops[hopid-1]
        self._hops[hopid-1] = Hop(mod_hop.hop_id, mod_hop.public_ip_address, mod_hop.port,
                                  mod_hop.transport_protocol, interface)
        self._log_current_config()

    def clear_hops(self):
        self.number_of_hops_in_current_cascading = 0
        self._hops.clear()
        self._log_current_config()

    def enable(self):
        with self._enable_disable_lock:
            self._logger.debug("enabling")
            if self._enabled:
                self._logger.debug("already enabled")
                return
            self._enabled = True
            self._update_firewall()

    def apply_changes(self):
        with self._enable_disable_lock:
            self._logger.debug("apply changes")
            self._update_firewall()

    def disable(self):
        with self._enable_disable_lock:
            self._logger.debug("disabling")
            if not self._enabled:
                self._logger.debug("already disabled")
                return
            self._disable_firewall()
            self._enabled = False

    def _update_firewall(self):
        if not self._enabled:
            self._logger.debug("not enabled, skipping update")
            return

        self._logger.info("adjusting firewall")
        rules = [
            "set skip on lo0",
            "block in all",
            "block out all",
        ]
        number_of_hop_rules = 0
        if self._primary_interface:
            for i, hop in enumerate(self._hops):
                try:
                    interface = self._primary_interface if i == 0 else self._hops[i-1].interface
                except IndexError:
                    interface = None
                public_ip_address = hop.public_ip_address
                port = hop.port
                transport_protocol = hop.transport_protocol

                if not interface or not port or not public_ip_address:
                    break

                number_of_hop_rules += 1
                rules.append(
                    "pass out on {interface} inet proto {transport_protocol} to {public_ip_address} port {port} keep state".format(
                        interface=interface, transport_protocol=transport_protocol,
                        public_ip_address=public_ip_address, port=port))

            if number_of_hop_rules == 0:
                self._logger.info("Notice: No VPN tunnel is active.")

            rules.extend([
                "pass out on {primary_interface} inet to 10.0.0.0/8".format(primary_interface=self._primary_interface),
                "pass in on {primary_interface} inet from 10.0.0.0/8".format(primary_interface=self._primary_interface),
                "pass out on {primary_interface} inet to 192.168.0.0/16".format(primary_interface=self._primary_interface),
                "pass in on {primary_interface} inet from 192.168.0.0/16".format(primary_interface=self._primary_interface),
                "pass out on {primary_interface} inet to 172.16.0.0/12".format(primary_interface=self._primary_interface),
                "pass in on {primary_interface} inet from 172.16.0.0/12".format(primary_interface=self._primary_interface),
                "pass out on {primary_interface} inet proto UDP to 224.0.0.251 port 5353".format(primary_interface=self._primary_interface),  # mDNS / local discovery
                "pass out on {primary_interface} inet to 169.254.0.0/16".format(primary_interface=self._primary_interface),  # link-local (works on primary interface only)
            ])
        else:
            self._logger.info("Notice: There's no active network connection")

        next_is_blocking_all_internet_traffic = True
        last_interface = None
        if number_of_hop_rules == self.number_of_hops_in_current_cascading:
            try:
                last_interface = self._hops[-1].interface
            except IndexError:
                last_interface = None
        if last_interface:
            rules.append("pass out on {interface} all keep state".format(interface=last_interface))
            next_is_blocking_all_internet_traffic = False
        else:
            self._logger.info("Notice: The VPN tunnel is not up. Blocking all traffic.")

        self._is_blocking_all_internet_traffic = next_is_blocking_all_internet_traffic

        self._logger.debug("last interface: {}".format(last_interface))
        self._logger.debug("number of hop rules: {}".format(number_of_hop_rules))
        self._logger.debug("len(hops): {}".format(len(self._hops)))
        self._logger.debug("number of hops in current cascading: {}".format(self.number_of_hops_in_current_cascading))
        self._logger.debug("is blocking all internet traffic: {}".format(self._is_blocking_all_internet_traffic))

        self._logger.debug("current firewall rules: {}".format(rules))

        try:
            fd, path = tempfile.mkstemp(prefix="pf_")
            f = os.fdopen(fd, "w")
            f.write("\n".join(rules) + "\n")
            f.close()
            self._logger.debug("wrote firewall rules to {}".format(path))

            self._logger.info("applying firewall rules")
            args = [PFCTL, "-f", path]
            self._logger.debug("executing: {}".format(" ".join(args)))
            pf_process = subprocess.Popen(args)
            pf_process.communicate()
            self._logger.debug("pfctl returned with exit code {}".format(pf_process.returncode))
            if pf_process.returncode != 0:
                self._logger.error("unable to apply firewall rules: pfctl returned with exit status {}".format(pf_process.returncode))
                raise Exception()

            self._logger.info("turning on firewall")
            args = [PFCTL, "-e"]
            self._logger.debug("executing: {}".format(" ".join(args)))
            pf_process = subprocess.Popen(args)
            pf_process.communicate()
            self._logger.debug("pfctl returned with exit code {}".format(pf_process.returncode))
            if pf_process.returncode != 0:
                pass
                #self._logger.error("unable to enable firewall: pfctl returned with exit status {}".format(pf_process.returncode))
                # TODO: enable/disable firewall
                #raise Exception()

            has_tcp_connection = False
            for hop in self._hops:
                has_tcp_connection = has_tcp_connection or hop.transport_protocol == TRANSPORT_PROTOCOL_TCP
            if has_tcp_connection:
                self._logger.info("flushing connection states")
                args = [PFCTL, "-F", "states"]
                self._logger.debug("executing: {}".format(" ".join(args)))
                pf_process = subprocess.Popen(args)
                pf_process.communicate()
                self._logger.debug("pfctl returned with exit code {}".format(pf_process.returncode))
                if pf_process.returncode != 0:
                    self._logger.error("unable to flush firewall connection states: pfctl returned with exit status {}".format(pf_process.returncode))
                    raise Exception()

        except Exception as e:
            self._logger.error("unexpected exception: {}".format(e))
            self._logger.debug(traceback.format_exc())
            reporter.report_error(traceback=traceback.format_exc())

        self.on_change.notify_observers(self)

    def _disable_firewall(self):
        # TODO: remember firewall state and revert
        self._is_blocking_all_internet_traffic = False
        self._logger.info("turning off firewall")
        args = [PFCTL, "-d"]
        self._logger.debug("executing: {}".format(" ".join(args)))
        pf_process = subprocess.Popen(args)
        pf_process.communicate()
        self._logger.debug("pfctl returned with exit code {}".format(pf_process.returncode))
        if pf_process.returncode != 0:
            self._logger.error(
                "unable to disable firewall: pfctl returned with exit status {}".format(pf_process.returncode))
        self.on_change.notify_observers(self)
