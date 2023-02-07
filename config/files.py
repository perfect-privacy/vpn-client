import os, sys
from .config import BRANCH
from .config import PLATFORM
from .constants import PLATFORMS
from .paths import APP_THIRDPARTY_DIR, APP_DIR, APP_VAR_DIR

branch = "_%s" % BRANCH.upper()
if branch == "_RELEASE": branch = ""
if PLATFORM == PLATFORMS.windows:
    SOFTWARE_UPDATE_FILENAME = "Perfect_Privacy%s_Setup.exe" % branch
if PLATFORM == PLATFORMS.macos:
    SOFTWARE_UPDATE_FILENAME = "Perfect_Privacy%s_Setup.dmg" % branch
if PLATFORM == PLATFORMS.linux:
    SOFTWARE_UPDATE_FILENAME = "Perfect_Privacy%s_Setup.run" % branch

CONFIG_UPDATE_FILENAME =  "Perfect_Privacy_App_Configs.zip"

TAPWINDOW_9_00_00_21_INF = os.path.join(APP_THIRDPARTY_DIR, "tapwindows", "9_00_00_21", "64", "tap0901.inf")
TAPWINDOW_9_00_00_9_INF = os.path.join(APP_THIRDPARTY_DIR, "tapwindows", "9_00_00_9", "64", "tap0901.inf")
TAPWINDOW_LATEST_INF = os.path.join(APP_THIRDPARTY_DIR, "tapwindows", "latest", "64", "tap0901.inf")
WINTUN_INF = os.path.join(APP_THIRDPARTY_DIR, "wintun", "latest", "64", "wintun.inf")
PNPUTIL = None
TAPCTL = None

if PLATFORM == PLATFORMS.windows:
    OPENVPN       = os.path.join(APP_THIRDPARTY_DIR, "openvpn", "2.5.0", "64", "pp.openvpn.exe")
    TAPCTL        = os.path.join(APP_THIRDPARTY_DIR, "openvpn", "2.5.0", "64", "pp.tapctl.exe" )
    SSH           = os.path.join(APP_THIRDPARTY_DIR, "stealth", "pp.plink.exe")
    OBFS          = os.path.join(APP_THIRDPARTY_DIR, "stealth", "pp.obfs4proxy.exe")
    STUNNEL       = os.path.join(APP_THIRDPARTY_DIR, "stealth", "pp.tstunnel.exe")
    PNPUTIL       = os.path.join(os.environ["WINDIR"], "system32", "pnputil.exe")
    if not os.path.exists(PNPUTIL):
        PNPUTIL   = os.path.join(os.environ["WINDIR"], "Sysnative", "pnputil.exe")
    ROUTE       = os.path.join(os.environ["WINDIR"], "system32", "ROUTE.exe")
    if not os.path.exists(ROUTE):
        ROUTE   = os.path.join(os.environ["WINDIR"], "Sysnative", "ROUTE.exe")
    NETSH       = os.path.join(os.environ["WINDIR"], "system32", "netsh.exe")
    if not os.path.exists(NETSH):
        NETSH   = os.path.join(os.environ["WINDIR"], "Sysnative", "netsh.exe")

if PLATFORM == PLATFORMS.macos:
    OPENVPN       = os.path.join(APP_THIRDPARTY_DIR, "openvpn", "2.5.0", "pp.openvpn")
    SSH       = os.path.join("/usr","bin", "ssh")
    OBFS          = os.path.join(APP_THIRDPARTY_DIR, "stealth", "pp.obfs4proxy")
    STUNNEL       = os.path.join(APP_THIRDPARTY_DIR, "stealth", "pp.stunnel")

if PLATFORM == PLATFORMS.linux:
    OPENVPN    = "/usr/sbin/openvpn"
    SSH        = "/usr/sbin/ssh"
    OBFS       = "/usr/sbin/obfsproxy"
    STUNNEL    = "/usr/sbin/stunnel"

REPORT_FILE   = os.path.join(APP_VAR_DIR, "reports")
SETTINGS_FILE = os.path.join(APP_VAR_DIR, "storage.db")

PID_FILE = "/var/run/perfect-privacy.pid" # fixme
LOG_FILE = "/var/log/perfect-privacy.log"

