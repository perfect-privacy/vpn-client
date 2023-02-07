from config.config import PLATFORM
from config.constants import PLATFORMS

if PLATFORM == PLATFORMS.windows:
    from .softwareupdater_windows import SoftwareUpdater_Windows as SoftwareUpdater

if PLATFORM == PLATFORMS.linux:
    from .softwareupdater_linux import SoftwareUpdater_Linux as SoftwareUpdater

if PLATFORM == PLATFORMS.macos:
    from .softwareupdater_macos import SoftwareUpdater_Macos as SoftwareUpdater

if PLATFORM == PLATFORMS.privacypi:
    from .softwareupdater_linux import SoftwareUpdater_Linux as SoftwareUpdater
