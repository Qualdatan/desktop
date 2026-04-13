; SPDX-License-Identifier: AGPL-3.0-only
;
; Qualdatan Desktop — NSIS-Installer-Template fuer Tauri 2.
;
; Dieses Template setzt auf Tauri's mitgeliefertem NSIS-Default auf und
; fuegt eine **optionale Komponente** "TUI Launcher" hinzu. Die Komponente
; installiert NICHT automatisch Python oder pipx — das waere nutzerfeindlich
; und setzt Python auf dem PATH voraus. Stattdessen wird lediglich ein
; Marker-File nach %LOCALAPPDATA%\Qualdatan\install_tui.flag geschrieben,
; damit die Desktop-App (oder ein Post-Install-Dialog) dem Nutzer das
; Nachinstallieren via `pipx install qualdatan-tui` anbieten kann.
;
; Tauri 2 rendert dieses Template via Tera; die ${...}-Platzhalter werden
; vom Tauri-Bundler ersetzt (siehe:
; https://v2.tauri.app/distribute/windows-installer/#customization).
;
; Upstream-Default:
; https://github.com/tauri-apps/tauri/blob/dev/crates/tauri-bundler/src/bundle/windows/nsis/installer.nsi
;
; Hinweis: Wenn dieses Template Felder verpasst, die der Upstream-Default
; liefert (Updater-Hooks, Uninstaller-Logik, WebView2-Bootstrap), muss es
; synchron gehalten werden. Solange Tauri-Upstream keine saubere
; Section-Injection-API bietet, ist ein Full-Override der pragmatische Weg.

Unicode true
ManifestDPIAware true

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "Sections.nsh"

;--------------------------------
; Tauri-injizierte Defines (vom Bundler ersetzt)
;--------------------------------
Name "${PRODUCTNAME}"
BrandingText "${BUNDLEID}"
OutFile "${OUTFILE}"
InstallDir "${INSTALLDIR}"
VIProductVersion "${VERSIONWITHBUILD}"
VIAddVersionKey "ProductName" "${PRODUCTNAME}"
VIAddVersionKey "CompanyName" "${MANUFACTURER}"
VIAddVersionKey "LegalCopyright" "${COPYRIGHT}"
VIAddVersionKey "FileDescription" "${PRODUCTNAME}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"

;--------------------------------
; Modern-UI-Seiten (inkl. Components-Page)
;--------------------------------
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LICENSEFILE}"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "German"

;--------------------------------
; Section 1 — Desktop App (PFLICHT, RO)
;--------------------------------
Section "Qualdatan Desktop App" SecDesktop
    SectionIn RO
    SetOutPath "$INSTDIR"

    ; Tauri-Bundler injiziert hier die eigentlichen Dateilisten via
    ; ${MAIN_APP_FILES} / ${RESOURCES} / ${BINARIES}. Da dieses Template
    ; als Override fungiert, rendern wir die Standard-Makros:
    !ifmacrodef "APP_ASSOCIATE"
        !insertmacro APP_ASSOCIATE
    !endif

    ; Main executable + resources (vom Bundler substituiert).
    File /r "${APPDIR}\*.*"

    ; Uninstaller schreiben.
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Registry-Eintraege fuer "Programme und Features".
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUNDLEID}" \
        "DisplayName" "${PRODUCTNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUNDLEID}" \
        "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUNDLEID}" \
        "Publisher" "${MANUFACTURER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUNDLEID}" \
        "UninstallString" "$\"$INSTDIR\uninstall.exe$\""

    ; Startmenue-Shortcut.
    CreateDirectory "$SMPROGRAMS\${PRODUCTNAME}"
    CreateShortcut "$SMPROGRAMS\${PRODUCTNAME}\${PRODUCTNAME}.lnk" "$INSTDIR\${MAINBINARYNAME}.exe"
SectionEnd

;--------------------------------
; Section 2 — TUI Launcher (OPTIONAL, default OFF)
;
; Schreibt nur einen Marker, damit die Desktop-App den Nutzer spaeter fragen
; kann: "TUI via pipx install qualdatan-tui jetzt einrichten?". Keine
; Python-Installation im NSIS-Scope.
;--------------------------------
Section /o "TUI Launcher (qualdatan-tui via pipx)" SecTUI
    SetShellVarContext current
    CreateDirectory "$LOCALAPPDATA\Qualdatan"
    FileOpen $0 "$LOCALAPPDATA\Qualdatan\install_tui.flag" w
    FileWrite $0 "requested=1$\r$\n"
    FileWrite $0 "version=${VERSION}$\r$\n"
    FileClose $0
SectionEnd

;--------------------------------
; Component-Descriptions (MUI-Tooltips)
;--------------------------------
LangString DESC_SecDesktop ${LANG_ENGLISH} "The Qualdatan Desktop application (required)."
LangString DESC_SecDesktop ${LANG_GERMAN}  "Die Qualdatan-Desktop-Anwendung (erforderlich)."
LangString DESC_SecTUI     ${LANG_ENGLISH} "Mark the optional TUI (qualdatan-tui) for later pipx installation. Requires Python 3.11+ on PATH."
LangString DESC_SecTUI     ${LANG_GERMAN}  "Markiert die optionale TUI (qualdatan-tui) fuer spaetere pipx-Installation. Erfordert Python 3.11+ auf PATH."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecTUI}     $(DESC_SecTUI)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
; Post-Install-Hinweis, wenn TUI-Komponente gewaehlt wurde
;--------------------------------
Function .onInstSuccess
    ${If} ${SectionIsSelected} ${SecTUI}
        MessageBox MB_OK|MB_ICONINFORMATION \
            "TUI-Komponente markiert.$\n$\n\
Zur Installation bitte in einer Shell ausfuehren:$\n$\n\
    pipx install qualdatan-tui$\n$\n\
(Voraussetzung: Python 3.11+ und pipx auf PATH.)"
    ${EndIf}
FunctionEnd

;--------------------------------
; Uninstaller
;--------------------------------
Section "Uninstall"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR"

    Delete "$SMPROGRAMS\${PRODUCTNAME}\${PRODUCTNAME}.lnk"
    RMDir  "$SMPROGRAMS\${PRODUCTNAME}"

    SetShellVarContext current
    Delete "$LOCALAPPDATA\Qualdatan\install_tui.flag"
    RMDir  "$LOCALAPPDATA\Qualdatan"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUNDLEID}"
SectionEnd
