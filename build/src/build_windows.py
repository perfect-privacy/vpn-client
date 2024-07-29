import os, sys
import subprocess
import shutil
import glob
from .build_common import BuildCommon

class BuildWindows(BuildCommon):
    def _copy_files(self):
        folder = self.PLATFORM
        if self.ARCH == "arm64" and self.PLATFORM == "windows":
            folder = "%s-arm64" % folder
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", folder, "openvpn")    , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "openvpn") )
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", folder, "stealth")    , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "stealth") )
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", folder, "tapwindows") , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "tapwindows") )
        if self.ARCH != "arm64":
            shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", folder, "wintun")     , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "wintun") )
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", folder, "dco")     , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "dco") )
        super(BuildWindows, self)._copy_files()
        os.rename(os.path.join(self.BUILD_DIR_TARGET, "perfect-privacy-frontend.exe")         , os.path.join(self.BUILD_DIR_TARGET, "perfect-privacy.exe"))

    def _create_installer(self):
        # set product version to env
        env = os.environ.copy()

        release_data = open(os.path.join(self.SOURCE_DIR, "config", "release.conf"), "r").read()
        APP_VERSION = release_data.split("APP_VERSION=")[1].split("\n")[0]
        env["PRODUCT_VERSION"] = "%s.%s" % (APP_VERSION, self.BUILDNUMBER)

        # run nsis install builder
        nsi_script = os.path.join(self.SOURCE_DIR, "build","data", "nsis", "setup.nsi")
        subprocess.call( args=["c:\\Program Files (x86)\\NSIS\\Bin\\makensis.exe", nsi_script], env=env)

        # move output file to target destination
        branch = "_%s" % self.BRANCH.upper()
        if branch == "_RELEASE":
            branch = ""
        arch = ""
        if self.ARCH == "arm64":
            arch = "_ARM64"
        outputfile = os.path.join(self.SOURCE_DIR, "build","data", "nsis", "Perfect_Privacy_Setup.exe")
        targetfile = os.path.join(self.SOURCE_DIR, "build_tmp", "Perfect_Privacy%s_Setup%s.exe"  % (branch, arch))
        if os.path.isfile(targetfile):
            os.remove(targetfile)
        os.rename(outputfile, targetfile )

        # create version file
        with open(os.path.join(self.SOURCE_DIR, "build_tmp", "Perfect_Privacy%s_Setup%s.exe.version" % (branch, arch)),"w") as f:
            f.write(APP_VERSION)

        print(targetfile, " CREATED")

