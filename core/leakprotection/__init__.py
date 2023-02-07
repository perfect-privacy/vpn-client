from config.config import PLATFORM
from config.constants import PLATFORMS

if PLATFORM == PLATFORMS.windows:
    from .leakprotection_windows import LeakProtection_windows as LeakProtection

if PLATFORM == PLATFORMS.linux:
    from .leakprotection_linux import LeakProtection_linux as LeakProtection

if PLATFORM == PLATFORMS.macos:
    from .leakprotection_macos import LeakProtection_macos as LeakProtection

if PLATFORM == PLATFORMS.privacypi:
    from .leakprotection_linux import LeakProtection_linux as LeakProtection


