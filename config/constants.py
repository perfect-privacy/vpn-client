#from enum import Enum

class PLATFORMS():
    windows   = "windows"
    linux     = "linux"
    macos     = "macos"
    raspberry = "raspberry"
    privacypi = "privacypi"

class BRANCHES():
    dev     = "dev"   # a tmp local version build by a dev on his machine
    beta    = "beta"  # public beta version, is in Branch "master"
    release = "release" # release version, is in Branch release

class VPN_PROTOCOLS():
    openvpn = "openvpn"
    ipsec   = "ipsec"

class OPENVPN_PROTOCOLS():
    tcp  = "tcp"
    udp  = "udp"

class OPENVPN_CIPHER():
    aes_128_cbc  = "AES-128-CBC"
    aes_256_cbc  = "AES-256-CBC"
    aes_128_gcm  = "AES-128-GCM"
    aes_256_gcm  = "AES-256-GCM"

class OPENVPN_TLS_METHOD():
    tls_auth  = "tls-auth"
    tls_crypt = "tls-crypt"

class OPENVPN_PORTS():
    class TLSAUTH():
        udp = [ 148, 149,  150, 151 ,1148, 1149, 1150, 1151 ]
        tcp = [ 142, 152,  300, 301, 1142, 1152 ]
    class TLSCRYPT():
        udp = [  44, 443, 4433 ]
        tcp = [  44, 443, 4433 ]


class OPENVPN_PROXY_MODE():
    http    = "http"
    socks   = "socks"

class OPENVPN_DRIVER():
    wintun       = "wintun"
    dco       = "dco"
    tap_windows6_latest = "tap-windows6 latest"
    tap_windows6_9_00_00_21 = "tap-windows6 9.0.0.21"
    tap_windows6_9_00_00_9  = "tap-windows6 9.0.0.9"

class STEALTH_METHODS():
    no_stealth    = "no_stealth"
    http    = "http"
    socks   = "socks"
    stunnel = "stunnel"
    ssh     = "ssh"
    obfs    = "obfs"

class STEALTH_PORTS():
    ssh     = [  22, 222]
    stunnel = [  53, 443, 8085, 9009, 36315]
    stunnel_tlscrypt = [  54, 442, 8084]
    obfs    = [  53, 443, 8085, 9009, 36315]
    obfs_tlscrypt = [  81, 444, 8088]
    socks    =[  21, 508, 5080]
    http    = [  3128, 8080]

class PROTECTION_SCOPES():
    disabled    = "disabled"
    tunnel    = "tunnel"
    program   = "program"
    permanent = "permanent"

