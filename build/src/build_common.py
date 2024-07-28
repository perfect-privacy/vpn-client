import glob
import os, sys
import shutil

import requests


class BuildCommon():
    def __init__(self):
        self.SOURCE_DIR  = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0]))), ".."))
        self.BUILD_DIR_TMP = os.path.join(self.SOURCE_DIR, "build_tmp")
        self.BUILD_DIR_TARGET = os.path.join(self.BUILD_DIR_TMP, "perfect-privacy")
        self.PLATFORM    = None
        self.FRONTEND    = None
        self.BRANCH      = None
        self.BUILDNUMBER = None

    def run(self):
        self._parse_commandline()
        self._prepare_directorys()
        self._run_pyinstaller()
        self._write_runtime_config()
        self.download_thirdparty()
        self._copy_files()
        self.download_configs()
        self._create_installer()

    def _parse_commandline(self):
        self.PLATFORM    = sys.argv[1]
        self.FRONTEND    = sys.argv[2]
        self.BRANCH      = sys.argv[3]
        self.BUILDNUMBER = sys.argv[4]

    def _prepare_directorys(self):
        if os.path.exists(self.BUILD_DIR_TMP): shutil.rmtree(self.BUILD_DIR_TMP)
        os.mkdir(self.BUILD_DIR_TMP)
        if os.path.exists(self.BUILD_DIR_TARGET): shutil.rmtree(self.BUILD_DIR_TARGET)
        os.mkdir(self.BUILD_DIR_TARGET)

    def _run_pyinstaller(self):
        os.chdir(self.BUILD_DIR_TMP)
        python = sys.executable
        if python.endswith(".exe"):
            python = "python"

        os.system("%s -m pip install -r %s " % (python, os.path.join(self.SOURCE_DIR, "requirements.txt")))
        if self.PLATFORM == "windows":
            os.system("%s -m pip install -r %s " % (python, os.path.join(self.SOURCE_DIR, "requirements_win.txt")))
        elif self.PLATFORM == "linux":
            os.system("%s -m pip install -r %s" % (python, os.path.join(self.SOURCE_DIR, "requirements_linux.txt")))
        elif self.PLATFORM == "macos" or self.PLATFORM == "macos-arm":
            os.system("%s -m pip install -r %s " % (python, os.path.join(self.SOURCE_DIR, "requirements_mac.txt")))

        cmd = '%s -m PyInstaller  "%s" -- perfect-privacy-service  "%s" "%s"' % (
            python,
            os.path.join(self.SOURCE_DIR, "build", "data/pyinstaller", "build-service.spec"),
            self.SOURCE_DIR,
            os.path.join(self.SOURCE_DIR, "launcher", "perfect_privacy_service.py")
        )
        print(cmd)
        os.system(cmd)
        os.system('%s -m PyInstaller "%s" -- perfect-privacy-frontend "%s" "%s"' % (
            python,
            os.path.join(self.SOURCE_DIR, "build", "data/pyinstaller", "build-frontend.spec"),
            self.SOURCE_DIR,
            os.path.join(self.SOURCE_DIR, "launcher", "perfect_privacy_frontend.py")
        ))
        os.system("deactivate")
        os.system("rm -r build_venv")

    def _write_runtime_config(self):
        f = open( os.path.join( self.BUILD_DIR_TARGET, "runtime.conf") , "w")
        f.write("SHARED_SECRET=REPLACE_TOKEN_ON_POST_INSTALL")
        f.close()

        release_data = open(os.path.join(self.SOURCE_DIR, "config", "release.conf"),"r").read()
        VERSION = release_data.split("APP_VERSION=")[1].split("\n")[0]
        f = open( os.path.join( self.BUILD_DIR_TARGET , "release.conf") , "w")
        f.write("FRONTEND=%s\n" % self.FRONTEND)
        f.write("APP_VERSION=%s\n" % VERSION)
        f.write("APP_BUILD=%s\n" % self.BUILDNUMBER)
        f.write("BRANCH=%s\n" % self.BRANCH)
        f.close()

    def download_configs(self):
        r = requests.get("https://www.perfect-privacy.com/downloads/Perfect_Privacy_App_Configs.zip")
        open( os.path.join(self.BUILD_DIR_TARGET, "var", "configs", "configs.zip"), "wb" ).write(r.content)
        if self.PLATFORM == "windows":
            os.system("cd \"%s\" & powershell -command \"Expand-Archive '%s'\"" % (os.path.join(self.BUILD_DIR_TARGET, "var", "configs"), "configs.zip"))
            for f in glob.glob(os.path.join(self.BUILD_DIR_TARGET, "var", "configs", "configs","Perfect_Privacy_App_Configs", "*")):
                shutil.move(f, os.path.join(self.BUILD_DIR_TARGET, "var", "configs" ))
            shutil.rmtree(os.path.join(self.BUILD_DIR_TARGET, "var", "configs", "configs"))
        else:
            os.system("cd \"%s\" &&  unzip '%s'" % (os.path.join(self.BUILD_DIR_TARGET, "var", "configs"), "configs.zip"))
            os.system("cd \"%s\" && mv Perfect_Privacy_App_Configs/* . && rm -r Perfect_Privacy_App_Configs" % os.path.join(self.BUILD_DIR_TARGET, "var", "configs"))
        os.remove(os.path.join(self.BUILD_DIR_TARGET, "var", "configs", "configs.zip"))

    def download_thirdparty(self):
        if not os.path.exists(os.path.join(self.SOURCE_DIR, "thirdparty", "thirdparty.zip")):
            r = requests.get("https://github.com/perfect-privacy/vpn-client/releases/download/ThirdpartySoftware/thirdparty.zip")
            open( os.path.join(self.SOURCE_DIR, "thirdparty", "thirdparty.zip"), "wb" ).write(r.content)
            if self.PLATFORM == "windows":
                os.system("cd \"%s\" & powershell -command \"Expand-Archive '%s'\"" % (os.path.join(self.SOURCE_DIR, "thirdparty"), "thirdparty.zip"))
                shutil.copytree(os.path.join(self.SOURCE_DIR, "thirdparty", "thirdparty", "windows"),os.path.join(self.SOURCE_DIR, "thirdparty", "windows"))
                shutil.copytree(os.path.join(self.SOURCE_DIR, "thirdparty", "thirdparty", "macos"),os.path.join(self.SOURCE_DIR, "thirdparty", "macos"))
                shutil.rmtree(os.path.join(self.SOURCE_DIR, "thirdparty", "thirdparty"))
            else:
                os.system("cd \"%s\" &&  unzip '%s'" % (os.path.join(self.SOURCE_DIR, "thirdparty"), "thirdparty.zip"))
        #os.remove(os.path.join(self.SOURCE_DIR, "thirdparty", "thirdparty.zip"))

    def _copy_files(self):
        # create var dirs
        os.mkdir(os.path.join(self.BUILD_DIR_TARGET, "var"))
        os.mkdir(os.path.join(self.BUILD_DIR_TARGET, "var", "software_update"))
        os.mkdir(os.path.join(self.BUILD_DIR_TARGET, "var", "config_update"))
        os.mkdir(os.path.join(self.BUILD_DIR_TARGET, "var", "configs"))
        #shutil.copytree(os.path.join(self.SOURCE_DIR, "var", "configs"), os.path.join(self.BUILD_DIR_TARGET, "var", "configs"))

        for f in glob.glob(os.path.join(self.BUILD_DIR_TMP, "dist", "perfect-privacy-service", "*")):
            try:
                if os.path.isdir(f):
                    shutil.copytree(
                        f,
                        os.path.join(self.BUILD_DIR_TARGET,os.path.split(f)[1]))
                else:
                    shutil.copy2(f, self.BUILD_DIR_TARGET)
            except:
                pass

        for f in glob.glob(os.path.join(self.BUILD_DIR_TMP, "dist", "perfect-privacy-frontend", "*")):
            print(f)
            try:
                if os.path.isdir(f):
                    shutil.copytree(
                        f,
                        os.path.join(self.BUILD_DIR_TARGET,os.path.split(f)[1]))
                else:
                    shutil.copy2(f, self.BUILD_DIR_TARGET)
            except:
                pass

        shutil.rmtree(os.path.join(self.SOURCE_DIR, "build_tmp", "build"))


    def _create_installer(self):
        raise NotImplementedError()
