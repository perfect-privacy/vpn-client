import os
import shutil
from .build_common import BuildCommon

class BuildLinux(BuildCommon):
    def _copy_files(self):
        target_dir = os.path.join(self.SOURCE_DIR, "build_tmp","dist", "perfect-privacy")
        shutil.copy(os.path.join(self.SOURCE_DIR, "build", "data/linux", "setup.sh"), target_dir)
        os.system('cp -ar "%s/build/data/linux/install_files" "%s/"' % (self.SOURCE_DIR, target_dir))
        super(BuildLinux, self)._copy_files()

    def _prepare_directorys(self):
        if os.path.exists(self.BUILD_DIR_TMP):
            os.system('rm -rf "%s"' % self.BUILD_DIR_TMP)
        os.mkdir(self.BUILD_DIR_TMP)

    def _create_installer(self):
        branch = "_%s" % self.BRANCH.upper()
        if branch == "_RELEASE":
            branch = ""
        cmd  ='makeself --needroot "%s/build_tmp/dist/perfect-privacy" %s/build_tmp/Perfect_Privacy%s_Setup.run "Perfect Privacy Installer" ./setup.sh' % (self.SOURCE_DIR, self.SOURCE_DIR ,branch)
        os.system(cmd)
        # create version file
        release_data = open(os.path.join(self.SOURCE_DIR, "config", "release.conf"), "r").read()
        APP_VERSION = release_data.split("APP_VERSION=")[1].split("\n")[0]
        with open(os.path.join(self.SOURCE_DIR, "build_tmp", "Perfect_Privacy%s_Setup.run.version" % branch), "w") as f:
            f.write(APP_VERSION)

