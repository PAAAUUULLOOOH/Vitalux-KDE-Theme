# Validation — Liquid Glass 1.0.0

Target: openSUSE Tumbleweed, Plasma/KWin 6.8.x, Wayland, x86_64.

Verified locally:

- Automated checks exercise real file/configuration restoration, repeat installs, fresh backup generations, later user changes, Firefox data preservation, JSON preferences, Steam file/symlink recovery, private Flatpak runtime paths, TeamSpeak launch arguments, GTK4 stylesheets, loader-file adoption and selective permission cleanup.
- System allowlists and archive path/link rejection are applied before staged writes.
- Missing/failed native builds cannot be reported as complete.
- The compositor guard refuses a binary for a different running KWin version.
- SDDM and splash QML loaded and rendered on QtQuick 6.12 / Mesa OpenGL ES 3.2 without QML/shader errors. This checks rendering, not authentication or a full Plasma session.
- All four Glass shader programs (downsample, upsample, noise and rounded refraction) compiled and linked using the KWin 6.8 GLSL preamble and SDF helper.
- 61 SVG assets were accepted by QtSvg. The original openSUSE Geeko source was separately checked for visible native rendering after viewport flattening.
- Native libXcursor accepted the 32px pointer and animated cursor files, including all 12 frames. Frame/file tables for every supplied size were checked.
- Bash/Python syntax, ZIP extraction and payload hashes were checked.
- Millennium 3.6.2's archive matched its official release checksum.

The complete native C++ build on openSUSE was not verified here. An official Tumbleweed 20261021 container was available, but its package repositories were inaccessible from the build environment. Pinned sources are included so the installer builds against the target's actual headers. The Plasma 6.8 drawWindow return-type change is handled explicitly.

Not exercised: a complete openSUSE session, SDDM authentication, Steam/Discord client sessions, the Flatpak client-loader bridge and the user's GPU. The installer/guard checks failures explicitly; successful local rendering does not prove every deployment works.
