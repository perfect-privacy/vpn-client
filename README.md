# Perfect Privacy Client


## Development

#### Install Dependencys
     
    pip install -r requirements.txt

On Windows also run:

    pip install -r requirements_win.txt


On MacOS also run:

    pip install -r requirements_mac.txt

Download third party (openvpn, obfsproxy, stunnel) binarys 
[zip(github)](https://github.com/perfect-privacy/vpn-client/releases/download/ThirdpartySoftwareUpdate/thirdparty.zip)
and unpack to thirdparty/


#### Running as Developer

In case a non dev version is running, stop background service first.
Windows:  

    "c:\Program Files (x86)\Perfect Privacy\perfect-privacy-service.exe" stop

MacOS:  

    launchctl unload /Library/LaunchDaemons/perfect-privacy-service.plist

Run standalone version as administrator/root, or as "system" user in windows for testing winTun Driver. 


    python launcher/standalone.py

#### Build installer package

    python build/build.py {Platform} {Frontend} {Branch} {BuildNumber}

    
- Platform: windows | macos
- Frontend: default 
- Branch: release | dev
- BuildNumber: set by jenkins or set to 0 on manual execution


    