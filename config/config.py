import os, sys, uuid
from .constants import PLATFORMS, BRANCHES

APP_NAME = "Perfect Privacy"

if getattr( sys, 'frozen', False ) == True:  # check if we are bundled by pyinstaller
    if "_internal" in sys._MEIPASS:
        RUNTIME_CONF = os.path.join(sys._MEIPASS, ".." ,"runtime.conf")
        RELEASE_CONF = os.path.join(sys._MEIPASS, ".." ,"release.conf")
    else:
        RUNTIME_CONF = os.path.join(sys._MEIPASS, "runtime.conf")
        RELEASE_CONF = os.path.join(sys._MEIPASS, "release.conf")

else:
    RUNTIME_CONF = os.path.join(os.path.dirname(os.path.realpath(__file__)), "runtime.conf")
    RELEASE_CONF = os.path.join(os.path.dirname(os.path.realpath(__file__)), "release.conf")

RUNTIME_CONF_DATA = {}
for key, value in [line.split("=") for line in open(RUNTIME_CONF, "r").read().strip().split("\n") if "=" in line ]:
    RUNTIME_CONF_DATA[key.strip()] = value.strip()
SHARED_SECRET    = RUNTIME_CONF_DATA["SHARED_SECRET"]
SERVICE_PORT     = 20420

if getattr( sys, 'frozen', False ) == True:  # check if we are bundled by pyinstaller
    content = open(RUNTIME_CONF, "r").read()
    if "REPLACE_TOKEN_ON_POST_INSTALL" in content:
        new_secret = "%s" % uuid.uuid4()
        content = content.replace("REPLACE_TOKEN_ON_POST_INSTALL", new_secret)
        try:
            with open(RUNTIME_CONF, "w") as f:
                f.write(content)
            SHARED_SECRET = new_secret
        except:
            print("Failed to write config")

RELEASE_CONF_DATA = {}
for key, value in [line.split("=") for line in open(RELEASE_CONF, "r").read().strip().split("\n") if "=" in line ]:
    RELEASE_CONF_DATA[key.strip()] = value.strip()

FRONTEND    = RELEASE_CONF_DATA["FRONTEND"]
APP_VERSION = RELEASE_CONF_DATA["APP_VERSION"]
APP_BUILD   = RELEASE_CONF_DATA["APP_BUILD"]
BRANCH      = RELEASE_CONF_DATA["BRANCH"]

APP_VERSION_FULL = "{version}-{branch} ({build}) ".format(version=APP_VERSION, branch=BRANCH, build=APP_BUILD).rstrip()
APP_IDENTIFIER   = "{name} {full_version}".format(name=APP_NAME, full_version=APP_VERSION_FULL)

PLATFORM = PLATFORMS.windows
if sys.platform.startswith("linux"):
    PLATFORM = PLATFORMS.linux
elif sys.platform.startswith("darwin"):
    PLATFORM = PLATFORMS.macos


SIG_PUBKEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAw89YGj7ROj7T/zH/eDmU
Do2tuzdMva3KYDS0PpRaaAgRnvnr6g42Dufl4Ht2wANM1MaishFZ7CZjdMqolPU2
EiumCKx4Gpc1bv78v14QLdh5GkHbtQWY919tiRe7AgbPZuvv5j+D9FjmV68pM/Zj
5EC99Cu9d2z004ub3z8dVTl17cOxIeGXtLY3xxc44JBVbaIQccdUbZPssdjdpb+m
fa2NtIpCt5/EHRgS8wjsxNqMfr+Lrj8y3STddlF3BOv+7sUcQ6km86yEBJb1cjal
eFD5xq/5mxAuxeKyrOK+ZOY1glXC9WOWqWCj7VYIEitXAYHuMBJygLlZrC1iok5i
6wIDAQAB
-----END PUBLIC KEY-----"""


FRONTEND_AUTORELOAD = BRANCH == BRANCHES.dev   # so we dont have to restart the app during frontend design so often

