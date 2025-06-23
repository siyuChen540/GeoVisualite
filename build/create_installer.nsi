; NSIS Installer Script for GeospatialTool

!define APP_NAME "GeospatialTool"
!define APP_VERSION "3.5"
!define COMPANY_NAME "Your Company"
!define EXE_NAME "GeospatialTool.exe"

; --- General ---
Name "${APP_NAME} ${APP_VERSION}"
OutFile "${APP_NAME}_${APP_VERSION}_Installer.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin ; 请求管理员权限

; --- Interface ---
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "..\icons\nl.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt" ; 你应该在项目根目录提供一个license.txt
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE_NAME}" ; 完成后运行程序
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese" ; 设置为简体中文

; --- Installer Section ---
Section "Install"
  SetOutPath $INSTDIR

  ; 将 PyInstaller 打包好的所有文件添加到安装程序中
  ; '..\dist\GeospatialTool\*.*' 是相对于此脚本的位置
  File /r "..\dist\GeospatialTool\*.*"

  ; --- Create Shortcuts ---
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"

  ; --- Write Registry for Uninstaller ---
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${EXE_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"

  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; --- Uninstaller Section ---
Section "Uninstall"
  ; --- Remove Files and Shortcuts ---
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  RMDir /r "$INSTDIR"

  ; --- Remove Registry Keys ---
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  DeleteRegKey HKLM "Software\${APP_NAME}"
SectionEnd