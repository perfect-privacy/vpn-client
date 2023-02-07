from config.config import PLATFORM
from config.constants import PLATFORMS


if PLATFORM == PLATFORMS.windows:
    from .stealth_ssh_windows import StealthSSHWindows as StealthSSH

if PLATFORM == PLATFORMS.linux:
    from .stealth_ssh_linux import StealthSSHLinux as StealthSSH

if PLATFORM == PLATFORMS.macos:
    from .stealth_ssh_mac import StealthSSHMacos as StealthSSH

if PLATFORM == PLATFORMS.privacypi:
    from .stealth_ssh_linux import StealthSSHLinux as StealthSSH


