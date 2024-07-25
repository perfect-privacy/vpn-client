import os
import shutil
from .build_common import BuildCommon

class BuildLinux(BuildCommon):
    def _copy_files(self):
        shutil.copy(os.path.join(self.SOURCE_DIR, "build", "data/linux", "setup.sh"), self.BUILD_DIR_TARGET)
        os.system('cp -ar "%s/build/data/linux/install_files" "%s/"' % (self.SOURCE_DIR, self.BUILD_DIR_TARGET))
        super(BuildLinux, self)._copy_files()
        os.rename(os.path.join(self.BUILD_DIR_TARGET, "perfect-privacy-frontend")         , os.path.join(self.BUILD_DIR_TARGET, "perfect-privacy"))

    def _create_installer(self):
        branch = "_%s" % self.BRANCH.upper()
        if branch == "_RELEASE":
            branch = ""
        cmd  ='makeself --needroot "%s/build_tmp/perfect-privacy" %s/build_tmp/Perfect_Privacy%s_Setup.run "Perfect Privacy Installer" ./setup.sh' % (self.SOURCE_DIR, self.SOURCE_DIR ,branch)
        os.system(cmd)
        # create version file
        release_data = open(os.path.join(self.SOURCE_DIR, "config", "release.conf"), "r").read()
        APP_VERSION = release_data.split("APP_VERSION=")[1].split("\n")[0]
        with open(os.path.join(self.SOURCE_DIR, "build_tmp", "Perfect_Privacy%s_Setup.run.version" % branch), "w") as f:
            f.write(APP_VERSION)

