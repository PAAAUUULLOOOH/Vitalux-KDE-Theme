# Validation — Vitalux Liquid Silver 1.1.1

Target: openSUSE Tumbleweed, Plasma/KWin 6.8.x, Wayland, x86_64.

Verified locally and in CI:

- Both executable desktop starters find their adjacent shell script in repository and standalone ZIP layouts, including local file URLs, spaces, apostrophes and Unicode in folder names.
- Graphical shell launches hand off to Konsole with the original arguments. Terminal output is saved privately; nonzero installer exit codes survive logging. Install and uninstall use separate logs without recursive terminal launches.
- Native builds use private writable source copies; upstream-generated shader files never modify the integrity-checked download. The standalone Kvantum CMake entry point now defines its color-scheme install destination.
- The openSUSE check reproduced the invalid `/usr/lib64/qt6/bin/qdbus` package request. The installer now requests `qt6-tools-qdbus` and also recognizes the Qt6 libexec location. System theme directories use readable permissions independently of the user's umask; backup and installer logs remain private.

- Every Liquid Silver palette value matches the pinned original Vitalux source. Original source files and their SHA-256 hashes are retained. The 3840 × 2160 lossless wallpaper was compared with an independent call to the original `premium.scene_pixmap(..., 'liquid_silver')` and is pixel-identical.
- The 1.0.0-to-1.1.0 upgrade applies the original silver accent and dark GTK preference while retaining the first pre-install backup for removal.
- All six application stylesheets use the original dark/silver colors. KDE and Plasma color-scheme files are identical.
- Automated checks exercise real file/configuration restoration, repeat installs, fresh backup generations, later user changes, Firefox data preservation, JSON preferences, Steam file/symlink recovery, private Flatpak runtime paths, TeamSpeak launch arguments, GTK4 stylesheets, loader-file adoption and selective permission cleanup.
- System allowlists and archive path/link rejection are applied before staged writes.
- Missing/failed native builds cannot be reported as complete.
- The compositor guard refuses a binary for a different running KWin version.
- SDDM and splash QML loaded and rendered on QtQuick 6.12 / Mesa OpenGL ES 3.2 without QML/shader errors. This checks rendering, not authentication or a full Plasma session.
- All four Glass shader programs (downsample, upsample, noise and rounded refraction) compiled and linked using the KWin 6.8 GLSL preamble and SDF helper.
- All 60 current SVG assets were accepted by QtSvg. The original openSUSE Geeko source was previously checked for visible native rendering after viewport flattening.
- The GTK3 CSS parser accepted the complete dark stylesheet without parsing errors.
- Native libXcursor accepted the 32px pointer and animated cursor files, including all 12 frames. Frame/file tables for every supplied size were checked.
- Bash/Python syntax, ZIP extraction and payload hashes were checked.
- Millennium 3.6.2's archive matched its official release checksum.

The complete C++ build and staging of Glass, Kvantum and Aurorae passed on openSUSE Tumbleweed / KWin 6.8.x in [GitHub Actions run 40015302285](https://github.com/PAAAUUULLOOOH/Vitalux-KDE-Theme/actions/runs/40015302285). All expected plugins and the Kvantum color scheme were present, all staged destinations passed the system allowlist, and the read-only source package retained its original integrity hashes. This is a build/install-plan check, not a live desktop installation. The 50 regression tests also passed.

The verified fixes cover the Tumbleweed Qt6 D-Bus package, compositor-free RPM version detection, the standalone Kvantum install destination, KWin 6.8 background-item and pixel-grid APIs, and writable build copies. Original visual materials remain unchanged.

Not exercised: a complete openSUSE session, SDDM authentication, Steam/Discord client sessions, the Flatpak client-loader bridge and the user's GPU. The installer/guard checks failures explicitly; successful local rendering does not prove every deployment works.

The native QtQuick previews show individual login/start components with an original preview motif. They are not presented as a complete Plasma session or an SDDM authentication test. Actual installed openSUSE branding is read from the target machine.
