
- windows/stealth/pp.obfs4proxy.exe  
    - https://www.torproject.org/download/  
    - download, install  
    - go to Installdir\Browser\TorBrowser\Tor\PluggableTransports and get obfs4proxy.exe  
    - rename to pp.obfs4proxy.exe   
    
- macos/stealth/pp.obfs4proxy  
    - https://www.torproject.org/download/  
    - download, install  
    - go to TorBrowser.app\Content\MacOS\Tor\PluggableTransports and get obfs4proxy  
    - rename to pp.obfs4proxy   
        
- windows/stealth/pp.tstunnel.exe
    - https://www.stunnel.org/downloads.html    
    - download, install
    - go to C:\Program Files (x86)\stunnel\bin, get tstunnel.exe and libssp-0.dll
    - rename to pp.tstunnel.exe
    
- macos/stealth/pp.tstunnel
    - brew install stunnel   
    - get /usr/local/bin/stunnel
    - rename to pp.tstunnel
        
- windows/stealth/plink.exe
    - https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    - download latest plink.exe 32 bit binary
    - https://the.earth.li/~sgtatham/putty/latest/w32/plink.exe
    - rename to pp.plink.exe
    
- windows/openvpn/
    - https://openvpn.net/community-downloads/
    - download 32 and 64 bit version
    - Open with 7zip explorer via -> "open internally *"
        - Open contained openvpn.cab via "open internally"
        - Files in archive have differnt names, extract and rename to
          -  tapctl.exe              -> pp.tapctl.exe
          -  bin.openvpn.exe         -> pp.openvpn.exe
          -  libcrypto_1_1.dll       -> libcrypto-1_1.dll
          -  liblzo2_2.dll           -> liblzo2-2.dll
          -  libpkcs11_helper_1.dll  -> libpkcs11-helper-1.dll
          -  libssl-1_1.dll          -> libssl-1_1.dll
            
- windows/wintun/latest
    - https://openvpn.net/community-downloads/
    - download 32 and 64 bit version
    - Open with 7zip explorer via -> "open internally *"
    - Open Binary.installer.dll.* via "open internally *",  there should be 2 such files, on is wintun, the other tap-windows6
    - go to .rsrc/RCDATA
    - For wintun, get and rename these files:
      -  WINTUN-WHQL.CAT      -> wintun.cat
      -  WINTUN-WHQL.INF      -> wintun.inf
      -  WINTUN-WHQL.SYS      -> wintun.sys     
         
- windows/tapwindows/latest
    - https://openvpn.net/community-downloads/
    - download 32 and 64 bit version
    - Open with 7zip explorer via -> "open internally *"
    - Open Binary.installer.dll.* via "open internally *",  there should be 2 such files, on is wintun, the other tap-windows6
    - go to .rsrc/RCDATA
    - For Tap-Windows6, get and rename these files:
       - DRIVER-WHQL.CAT      -> tap0901.cat
       - DRIVER-WHQL.INF      -> tap0901.inf
       - DRIVER-WHQL.SYS      -> tap0901.sys
   
   
- macos/openvpn/openvpn
    - Download and install tunnelblick 
    - get openvpn binary from Tunnelblick.app/Content/Resources/openvpn/
    
 
Or download https://github.com/perfect-privacy/vpn-client/releases/download/ThirdpartySoftwareUpdate/thirdparty.zip
 ready to use. 
 
