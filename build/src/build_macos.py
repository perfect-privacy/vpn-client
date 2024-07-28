import os, sys
import shutil
from .build_common import BuildCommon

class BuildMacos(BuildCommon):
    def _run_pyinstaller(self):
        super()._run_pyinstaller()
        #os.mkdir(os.path.join(self.BUILD_DIR_TARGET, "tk"))
        #os.mkdir(os.path.join(self.BUILD_DIR_TARGET, "tcl"))
        #os.system("cp -R /Library/Frameworks/Python.framework/Versions/3.8/lib/Tk8.6/*  '%s'" % os.path.join(self.BUILD_DIR_TARGET,  "tk"))
        #os.system("cp -R /Library/Frameworks/Python.framework/Versions/3.8/lib/tcl8.6/* '%s'" % os.path.join(self.BUILD_DIR_TARGET, "tcl"))

    def _copy_files(self):
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", "macos", "openvpn")    , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "openvpn") )
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", "macos", "stealth")    , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "stealth") )
        shutil.copytree( os.path.join(self.SOURCE_DIR, "thirdparty", "macos", "stealth-arm")    , os.path.join(self.BUILD_DIR_TARGET, "thirdparty", "stealth-arm") )
        super()._copy_files()
        os.rename(os.path.join(self.BUILD_DIR_TARGET, "perfect-privacy-frontend")         , os.path.join(self.BUILD_DIR_TARGET, "perfect-privacy"))

    def _create_installer(self):
        branch = "_%s" % self.BRANCH.upper()
        if branch == "_RELEASE":
            branch = ""
        release_data = open(os.path.join(self.SOURCE_DIR, "config", "release.conf"), "r").read()
        APP_VERSION = release_data.split("APP_VERSION=")[1].split("\n")[0]
        subname = ""
        if self.PLATFORM == "macos-arm":
            subname = "_ARM"
        with open(os.path.join(self.SOURCE_DIR, "build_tmp", "Perfect_Privacy%s_Setup%s.pkg.version" % (branch, subname)), "w") as f:
            f.write(APP_VERSION)

        self._create_uninstaller()

        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "app"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents", "MacOS"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents", "Resources"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg", "package"))

        cmd = 'cp -fR "%s" "%s"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "installer", "scripts" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg"))
        os.system(cmd)
        cmd = 'cp -fR "%s" "%s"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "installer", "resources" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg"))
        os.system(cmd)
        cmd = 'cp -fR "%s" "%s/"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "installer", "distribution.xml" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg"))
        os.system(cmd)
        cmd = 'cp -fR "%s" "%s/"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "installer", "Info.plist" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents"))
        os.system(cmd)
        cmd = 'cp -fR "%s"/* "%s"' % (os.path.join(self.SOURCE_DIR, "build_tmp", "perfect-privacy" ) , os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents", "MacOS") )
        os.system(cmd)
        cmd = 'cp -fR "%s" "%s"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "installer", "perfect-privacy-service.plist" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents", "MacOS", "perfect-privacy-service.plist"))
        os.system(cmd)
        cmd = 'cp -fR "%s" "%s"' % (os.path.join(self.SOURCE_DIR, "build_tmp", "perfect-privacy", "gui", "default", "static", "icons", "pp_icons.icns" ),  os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents", "Resources", "AppIcons.icns")  )
        os.system(cmd)
        os.system('cp -fR "%s" "%s"' % (os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller" , "uninstall.pkg"), os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app" )))
        os.system('rm -rf "%s" ' %  os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller" ))
        os.system('cd "%s" ; ln -s MacOS Frameworks' % os.path.join(self.BUILD_DIR_TMP, "pkg", "app", "Applications", "Perfect Privacy.app", "Contents"))

        os.system('chmod -R 755 "%s/pkg/scripts/postinstall"' % self.BUILD_DIR_TMP)
        os.system('chmod -R 755 "%s/pkg/scripts/preinstall"'  % self.BUILD_DIR_TMP)
        os.system('chmod -R 755 "%s/pkg/distribution.xml"'    % self.BUILD_DIR_TMP)
        os.system('chmod -R 755 "%s/pkg/resources"'           % self.BUILD_DIR_TMP)

        cmd = 'pkgbuild --identifier org.perfect-privacy.%(version)s \
            --version %(version)s                \
            --scripts "%(target_dir)s/pkg/scripts"    \
            --root    "%(target_dir)s/pkg/app"        \
            "%(target_dir)s/pkg/package/perfect-privacy.pkg"' % {
                "target_dir" : self.BUILD_DIR_TMP,
                "version"    : APP_VERSION
            }
        print(cmd)
        os.system(cmd)

        cmd = 'productbuild \
            --distribution "%(target_dir)s/pkg/distribution.xml" \
            --resources    "%(target_dir)s/pkg/resources"    \
            --package-path "%(target_dir)s/pkg/package"      \
            "%(target_dir)s/Perfect_Privacy%(branch)s_Setup%(subname)s.pkg"' % {
                "target_dir" : self.BUILD_DIR_TMP,
                "branch"     : branch,
                "subname"    : subname,
            }
        print(cmd)
        os.system(cmd)

    def _create_uninstaller(self):
        branch = "_%s" % self.BRANCH.upper()
        if branch == "_RELEASE":
            branch = ""
        release_data = open(os.path.join(self.SOURCE_DIR, "config", "release.conf"), "r").read()
        APP_VERSION = release_data.split("APP_VERSION=")[1].split("\n")[0]


        os.system('rm -rf "%s"' % os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller", "app"))
        os.mkdir(os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller", "package"))

        cmd = 'cp -r "%s" "%s"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "uninstaller", "scripts" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller"))
        os.system(cmd)
        cmd = 'cp -r "%s" "%s"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "uninstaller", "resources" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller"))
        os.system(cmd)
        cmd = 'cp -r "%s" "%s/"' % (os.path.join(self.SOURCE_DIR, "build", "data", "macos", "uninstaller", "distribution.xml" ) ,  os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller"))
        os.system(cmd)

        #content = open(os.path.join(self.SOURCE_DIR, "package_tmp", "pkg", "resources", "uninstall.sh" ),"r").read()
        #content.replace("__VERSION__", APP_VERSION)
        #open(os.path.join(self.SOURCE_DIR, "package_tmp", "pkg", "app", "Applications", "perfect-privacy", "uninstall.sh" ),"w").write(content)

        os.system('chmod -R 755 "%s/pkg_uninstaller/scripts/postinstall"' % self.BUILD_DIR_TMP)
        os.system('chmod -R 755 "%s/pkg_uninstaller/scripts/preinstall"'  % self.BUILD_DIR_TMP)
        os.system('chmod -R 755 "%s/pkg_uninstaller/distribution.xml"'    % self.BUILD_DIR_TMP)
        os.system('chmod -R 755 "%s/pkg_uninstaller/resources"'           % self.BUILD_DIR_TMP)

        target_dir = os.path.join(self.BUILD_DIR_TMP, "pkg_uninstaller")

        cmd = 'pkgbuild --identifier org.perfect-privacy.%(version)s \
            --version %(version)s                \
            --scripts "%(target_dir)s/scripts"    \
            --root    "%(target_dir)s/app"        \
            "%(target_dir)s/package/perfect-privacy-uninstall.pkg"' % {
                "target_dir" : target_dir,
                "version"    : APP_VERSION
            }
        print(cmd)
        os.system(cmd)
        cmd = 'productbuild \
            --distribution "%(target_dir)s/distribution.xml" \
            --resources    "%(target_dir)s/resources"    \
            --package-path "%(target_dir)s/package"      \
            "%(target_dir)s/uninstall.pkg"' % {
                "target_dir" : target_dir,
                "branch"     : branch
            }
        print(cmd)
        os.system(cmd)