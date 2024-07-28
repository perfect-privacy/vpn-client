import sys, os
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT_DIRECTORY))

from build.src import BuildWindows, BuildMacos, BuildLinux

def print_help():
    print ('''
    build.py <platform> <frontend> <branch> <buildnumber>
    branch   : release | dev
    buildnumber: set by jenkins or 0 on tests
''')

if __name__ == "__main__":
    PLATFORM = sys.argv[1]
    build = None

    if PLATFORM == "windows":
        build = BuildWindows()

    elif PLATFORM == "linux" or PLATFORM == "linux-arm64":
        build = BuildLinux()

    elif PLATFORM == "macos" or PLATFORM == "macos-arm":
        build = BuildMacos()

    #elif PLATFORM == "raspberry":
    #    build = BuildRaspberry()

    #elif PLATFORM == "privacypi":
    #    build = BuildPrivacypi()
    else:
        print_help()
        print("Unknown PLATFORM %s" % PLATFORM)

    build.run()
