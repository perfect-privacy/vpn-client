
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
      OR git clone git@github.com:Yawning/obfs4.git
      - cd obfs4 
      -  go build -o obfs4proxy/obfs4proxy ./obfs4proxy
      - 

- windows/stealth/pp.tstunnel.exe
    - https://www.stunnel.org/downloads.html    
    - download, install
    - go to C:\Program Files (x86)\stunnel\bin, get tstunnel.exe and dll files
    - rename to pp.tstunnel.exe
    
- macos/stealth/pp.stunnel
    - download stunnel src https://www.stunnel.org/downloads.html
    - ./configure --with-ssl=/opt/homebrew/opt/openssl/ ; make ; 
    - get src/stunnel , rename to pp.stunnel
        
- windows/stealth/plink.exe
    - https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
    - download latest plink.exe 32 bit binary
    - https://the.earth.li/~sgtatham/putty/latest/w32/plink.exe
    - rename to pp.plink.exe
    
- windows/openvpn/
    - https://openvpn.net/community-downloads/
    - download 64 bit version
    - Open with 7zip explorer via -> "open internally *"
        - Open contained openvpn.cab via "open internally"
        - Files in archive have differnt names, extract and rename to
          -  tapctl.exe              -> pp.tapctl.exe
          -  bin.openvpn.exe         -> pp.openvpn.exe
          -  libcrypto_3_x64.dll   -> libcrypto-3-x64.dll
          -  libpkcs11_helper_1.dll  -> libpkcs11-helper-1.dll
          -  libssl_3_x64.dll      -> libssl-3-x64.dll
          -  wcruntime140.dll for tapcat
            
- windows/wintun/latest
    - https://openvpn.net/community-downloads/
    - download 64 bit version
    - Open with 7zip explorer via -> "open internally *"
    - Open Binary.installer.dll.* via "open internally *",  there should be 2 such files, on is wintun, the other tap-windows6
    - go to .rsrc/RCDATA
    - For wintun, get and rename these files:
      -  WINTUN-WHQL.CAT      -> wintun.cat
      -  WINTUN-WHQL.INF      -> wintun.inf
      -  WINTUN-WHQL.SYS      -> wintun.sys     
         
- windows/tapwindows/latest
    - https://openvpn.net/community-downloads/
    - download 64 bit version
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
    
 
Or download https://github.com/perfect-privacy/vpn-client/releases/download/ThirdpartySoftware/thirdparty.zip
 ready to use. 
 
