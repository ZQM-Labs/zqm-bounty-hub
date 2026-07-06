# Mobile App Testing

Recommended libraries and tools:
- `adb` — Android device bridge interaction for installed apps
- `apktool` / `jadx` / `META-INF` inspection — local APK analysis
- `frida` / `objection` — runtime instrumentation for Android/iOS
- `mobsf` — static/dynamic mobile security framework
- `mitmproxy` / `burp` proxy chains — HTTPS interception for mobile traffic
- ` objection` REPL — runtime method tracing and SSL pinning bypass checks if authorized
- `apksigner` / `zipalign` — signing and rebuild boundaries
- `scrcpy` — device screen mirroring during manual dynamic testing

Process defaults:
- Static triage first: manifest, exported activities, network security config, signing.
- Dynamic triage second: proxy-intercept, storage analysis, IPC surfaces.
- Always check program scope for mobile binary testing; some programs restrict it.

Windows host tool availability:
- `frida` + `frida-tools`: installed and importable
- `objection`: installed and importable
- `adb`: installed at `C:\Users\zqmco\Documents\bounty-tools\_android\platform-tools\adb.exe`
- `jadx`: installed at `C:\Users\zqmco\Documents\bounty-tools\_android\bin\jadx` with JRE bundle in `_android\jdk-21.0.5+11-jre`
- `apktool`: installed as `apktool.jar` at `C:\Users\zqmco\Documents\bounty-tools\_android\apktool.jar`
- `mobsf`: not installed on this host
- Mobile dynamic testing still requires physical device/emulator and authorized scope

Evidence requirements:
- Save package name, version, test device/OS, and timeframe.
- Capture proxy logs and stack traces with secrets masked.
- Do not exfiltrate app data beyond scope findings.

Windows notes:
- `adb` install via `winget` or Android SDK Platform-Tools.
- `jadx` runs via Java; verify JRE availability before use.
- `frida`/`objection` use `pip` or prebuilt binaries; keep isolated from venv conflicts.
