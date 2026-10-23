# Sources, licenses and marks

Original theme artwork, icons/cursors, wallpaper, QML, stylesheets and installer code: MIT, copyright 2026 PAAAUUULLOOOH. See LICENSE.

## Bundled third-party source

This archive is a collection of separately licensed components. The MIT license does not replace these licenses. Original copyright/SPDX notices remain in the source files.

| Directory | Upstream | License and changes |
|---|---|---|
| vendor/kwin-effects-glass | https://github.com/Nael-Nathanael/kwin-effects-glass, fork of https://github.com/4v3ngR/kwin-effects-glass and KDE's blur effect | GPL-3.0 collection with per-file GPL-2.0-or-later notices; full text in LICENSE. Plasma 6.8 bool-return compatibility and C++23 selection added. |
| vendor/Kvantum | https://github.com/tsujan/Kvantum | GPL-3.0-or-later, full text in COPYING. Original style/default resources retained; minimal style-only CMake entry point. |
| vendor/aurorae-v2 | https://github.com/KDE/aurorae, tag v6.8.0 | Original v2 renderer, per-file GPL-2.0-or-later and BSD-3-Clause. Texts in LICENSES/. Minimal renderer-only entry point for missing distro plugins. |

Exact commits and modifications are recorded in each UPSTREAM.json. The directories contain the corresponding source used by the build scripts. Distribution-provided Qt/KDE libraries retain their licenses; no Qt/KDE runtime binary is redistributed here.

## External app-loader downloads

These binaries are not bundled. Pinned official URLs, names and SHA-256 hashes are in external-manifest.json. A missing app extension requires confirmation in the installer.

- Vencord Installer v1.4.2: https://github.com/Vencord/Installer/releases/tag/v1.4.2 — GPL-3.0. Source/license: https://github.com/Vencord/Installer/tree/v1.4.2
- Vencord client code fetched by its official installer: https://github.com/Vendicated/Vencord — GPL-3.0.
- Millennium v3.6.2: https://github.com/SteamClientHomebrew/Millennium/releases/tag/v3.6.2 — MIT. Source/license: https://github.com/SteamClientHomebrew/Millennium/tree/v3.6.2

The Flatpak Steam runtime placement and launcher integration are this project's adapter, not an officially endorsed Millennium installation method.

## Locally installed resources and marks

Plasma, KWin, KSvg, Breeze, GTK/Adwaita and installed applications are not relicensed by this theme. Icons inherit local Breeze resources; GTK3 imports the local Adwaita base.

Application/distribution icons are read from installed packages and combined locally with an original glass plate. Their original glyphs/colors and rights remain intact. The MIT license grants no rights to those marks. No Apple artwork, proprietary font or original openSUSE logo file is included in the ZIP.

openSUSE/Geeko sources and guidelines:
https://github.com/openSUSE/artwork/tree/master/logos/official
https://en.opensuse.org/openSUSE:Artwork_brand
https://en.opensuse.org/openSUSE:Trademark_guidelines

The official-logo directory marks its artwork as all rights reserved. Firefox/Mozilla, Discord, Steam/Valve, TeamSpeak, ProtonPlus, Haruna/KDE and other application marks retain their owners' rights.

Apple and Liquid Glass identify visual inspiration only. This project is independent and not endorsed by Apple, openSUSE, KDE or application vendors. Native QML previews use this project's original ring motif; installation substitutes the locally installed distribution mark.
