from .leakprotection_generic import LeakProtection_Generic

'''
# BLOCK SNMP/UPNP
# BLOCK ROUTER
# ALLOW LAN
# ALLOW TO LOWEST HOP IP
# ALLOW FROM LOCAL VPN IPS TO INTERNET
# DENY ALL TO INTERNET

'''
class LeakProtection_linux(LeakProtection_Generic):pass
