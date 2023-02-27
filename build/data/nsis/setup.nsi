#SetCompressor /SOLID lzma
requestexecutionlevel user

#
# Includes
#

!include "FileFunc.nsh"
!include LogicLib.nsh
!include "StrFunc.nsh"
!insertmacro Locate 



#
# CONSTANTS
#


!define MAIN_FILE 'perfect-privacy.exe'
!define PRODUCT_NAME "Perfect Privacy"
!define PRODUCT_PUBLISHER "Perfect Privacy"
!define PRODUCT_WEB_SITE "https://www.perfect-privacy.com/"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_NAME}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_VERSION "$%PRODUCT_VERSION%"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

!define OUTPUTFILENAME  "Perfect_Privacy_Setup.exe"


# 
# Icon
#

!define MUI_ICON "installer_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP  "headericon.png"
!define MUI_HEADERIMAGE_RIGHT


#
# Version Number Setup
#

VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "FileDescription" "Setup for ${PRODUCT_NAME}"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIProductVersion "${PRODUCT_VERSION}"


#
# Setup Output filename and install dir
#


Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${OUTPUTFILENAME}"
InstallDir "$PROGRAMFILES\Perfect Privacy"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails hide
ShowUnInstDetails hide





!include "MUI2.nsh"
!include UAC.nsh

; MUI Settings
!define MUI_ABORTWARNING
;!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Language Selection Dialog Settings
!define MUI_LANGDLL_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION PageFinishRun
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"
ReserveFile '${NSISDIR}\Plugins\x86-ansi\InstallOptions.dll'


Function PageFinishRun
    IfSilent +2 +1
    !insertmacro UAC_AsUser_ExecShell "" "$INSTDIR\${MAIN_FILE}" "" "" ""
FunctionEnd



!macro Init thing
uac_tryagain:
!insertmacro UAC_RunElevated
${Switch} $0
${Case} 0
	${IfThen} $1 = 1 ${|} Quit ${|} ;we are the outer process, the inner process has done its work, we are done
	${IfThen} $3 <> 0 ${|} ${Break} ${|} ;we are admin, let the show go on
	${If} $1 = 3 ;RunAs completed successfully, but with a non-admin user
		MessageBox mb_YesNo|mb_IconExclamation|mb_TopMost|mb_SetForeground "This ${thing} requires admin privileges, try again" /SD IDNO IDYES uac_tryagain IDNO 0
	${EndIf}
	;fall-through and die
${Case} 1223
	MessageBox mb_IconStop|mb_TopMost|mb_SetForeground "This ${thing} requires admin privileges, aborting!"
	Quit
${Case} 1062
	MessageBox mb_IconStop|mb_TopMost|mb_SetForeground "Logon service not running, aborting!"
	Quit
${Default}
	MessageBox mb_IconStop|mb_TopMost|mb_SetForeground "Unable to elevate , error $0"
	Quit
${EndSwitch}

SetShellVarContext all
!macroend




#
# INSTALL
#


Function .onInit
	System::Call 'kernel32::OpenMutex(i 0x100000, b 0, t "Perfect Privacy.SingleInstance") i .R0'
	IntCmp $R0 0 notRunning
		System::Call 'kernel32::CloseHandle(i $R0)'
		MessageBox MB_OK|MB_ICONEXCLAMATION "Perfect Privacy is running. Please close it first" /SD IDOK
		Abort
	notRunning:
	  !insertmacro Init "installer"
FunctionEnd

Section "Perfect Privacy" SEC_MAIN
    SectionIn RO
    SetOutPath "-"
    SetOverwrite on
    Var /GLOBAL switch_overwrite
    StrCpy $switch_overwrite 1

    nsExec::ExecToStack  '"$INSTDIR\perfect-privacy-service.exe" stop   ' # windows service stop
    #nsExec::ExecToStack  '"$INSTDIR\perfect-privacy-service.exe" remove ' # windows service uninstall
    Sleep 3000
    nsExec::ExecToStack  "TaskKill /IM perfect-privacy-service.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM perfect-privacy.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.tapctl.exe /F"     # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.openvpn.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.obfs4proxy.exe /F"  # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.plink.exe /F"       # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.tstunnel.exe /F"    # kill if needed

    nsExec::ExecToStack  "TaskKill /IM perfect-privacy-service.exe /F"    # doublekill if needed
    nsExec::ExecToStack  "TaskKill /IM perfect-privacy.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.tapctl.exe /F"     # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.openvpn.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.obfs4proxy.exe /F"  # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.plink.exe /F"       # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.tstunnel.exe /F"    # kill if needed

    CopyFiles /SILENT /FILESONLY $INSTDIR\var\storage.db $TEMP
    RMDir /r /REBOOTOK $INSTDIR

    File /r ..\..\..\build_tmp\perfect-privacy\*

    CreateDirectory "$SMPROGRAMS\Perfect Privacy"
    CreateShortCut  "$SMPROGRAMS\Perfect Privacy\Perfect Privacy.lnk" "$INSTDIR\perfect-privacy.exe"
    CreateShortCut  "$SMPROGRAMS\Perfect Privacy\Uninstall.lnk"       "$INSTDIR\uninstall.exe"
    CreateShortCut  "$DESKTOP\Perfect Privacy.lnk"                    "$INSTDIR\perfect-privacy.exe"

    CopyFiles /SILENT /FILESONLY $TEMP\storage.db $INSTDIR\var

    nsExec::ExecToStack '"$INSTDIR\perfect-privacy-service.exe" --startup auto install' # install windows service
    nsExec::ExecToStack '"$INSTDIR\perfect-privacy-service.exe" start'                  # start windows service

    Sleep 4000 # wait some time so background service is started before we launch frontend in next step


SectionEnd

Section -Post
    WriteUninstaller "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${MAIN_FILE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${MAIN_FILE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd





#
# UNINSTALL
#


Function un.onUninstSuccess
  HideWindow
FunctionEnd

Function un.onInit
	System::Call 'kernel32::OpenMutex(i 0x100000, b 0, t "Perfect Privacy.SingleInstance") i .R0'
	IntCmp $R0 0 notRunning
		System::Call 'kernel32::CloseHandle(i $R0)'
		MessageBox MB_OK|MB_ICONEXCLAMATION "Perfect Privacy is running. Please close it first" /SD IDOK
		Abort
	notRunning:
	  !insertmacro Init "uninstaller"
	  !insertmacro MUI_UNGETLANGUAGE
FunctionEnd

Section Uninstall
    nsExec::ExecToStack  '"$INSTDIR\perfect-privacy-service.exe" stop '      # windows service stop
    nsExec::ExecToStack  '"$INSTDIR\perfect-privacy-service.exe" remove '    # windows service uninstall
    nsExec::ExecToStack  '"$INSTDIR\perfect-privacy-service.exe" uninstall ' # disable firewall/network and eveything we installed

    nsExec::ExecToStack  "TaskKill /IM perfect-privacy-service.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM perfect-privacy.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.tapctl.exe /F"     # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.openvpn.exe /F"    # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.obfs4proxy.exe /F"  # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.plink.exe /F"       # kill if needed
    nsExec::ExecToStack  "TaskKill /IM pp.tstunnel.exe /F"    # kill if needed

	Delete "$DESKTOP\Perfect Privacy.lnk"
	RMDir /r /REBOOTOK "$INSTDIR"
	RMDir /r /REBOOTOK "$SMPROGRAMS\Perfect Privacy"
	DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
	DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
	SetAutoClose true
SectionEnd


#
# Lang
#

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN} "Install Perfect Privacy"
!insertmacro MUI_FUNCTION_DESCRIPTION_END
