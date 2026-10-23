# Liquid Glass · openSUSE

**[Download the installable ZIP](https://github.com/PAAAUUULLOOOH/Vitalux-KDE-Theme/raw/refs/heads/main/downloads/Liquid-Glass-openSUSE-1.0.0.zip)** · [SHA-256](downloads/Liquid-Glass-openSUSE-1.0.0.zip.sha256)

The ZIP includes `install.sh`, `uninstall.sh`, the theme files, application integrations and native component sources. The repository also contains the unpacked source under [`package/`](package/) and isolated automated checks under [`tests/`](tests/).

A coordinated KDE theme for **openSUSE Tumbleweed, Plasma/KWin 6.8.x, Wayland and x86_64**. Clear glass, actual shader-based refraction, soft light edges, blue accents and an original 4K wallpaper. Includes the artwork, application integrations and sources for building the matching native components on your machine.

This is an independent adaptation of the Liquid Glass visual language. Apple's renderer, proprietary fonts and wallpapers are not included.

## Installation

Extract the ZIP, close Discord and Steam, and open a terminal in the extracted folder. Run as your normal desktop user:

    bash install.sh

The installer checks the archive, installs build dependencies from your configured openSUSE repositories, builds the native components against your installed KWin, saves the original settings and applies the theme. It requests sudo only for system components. Missing Discord/Steam theme loaders are explained and require confirmation before installation. Downloads use pinned official release URLs and SHA-256 verification. Internet access is required.

Log out and back in once. The installer does not terminate your apps or restart the display manager.

    # Inspect the package and target system:
    bash install.sh --check

    # Keep Firefox chrome unchanged:
    bash install.sh --no-firefox

## Removal

    bash uninstall.sh

Original user files/settings are journaled in ~/.local/state/liquid-glass-kde (or your XDG state location). System components have a separate root-owned journal in /var/lib/liquid-glass-kde. Uninstall preserves unrelated settings and subsequent manual changes. It restores Steam files/links and the SDDM choice, and removes app loaders added by this installer. Existing loaders are retained. Distribution build dependencies remain installed.

## Included components

| Component | Integration |
|---|---|
| Global KDE theme | Plasma surfaces, full light palette, consistent blue accent and editable SVG artwork |
| Glass compositor | Bundled Glass KWin source with Plasma 6.8 compatibility; refraction, blur and specular rim |
| Qt applications | Kvantum Qt6 theme and style-engine source; existing compatible engines reused |
| Window decorations | Aurorae glass frames; original Aurorae v2 renderer source if the distro plugin is missing |
| Icons | Places/file-type artwork and glass presentation of locally installed application/openSUSE icons |
| Pointer | Original 24/32/48/64/96 px cursors, including animated wait/progress |
| Startup | Animated splash using the locally installed openSUSE mark |
| Lock screen | Matching wallpaper and system palette with native Plasma 6.8 authentication |
| Login | Qt6 SDDM theme with frosted controls, distribution mark, session selector and matching cursor |
| GTK 3/4 | Rounded styling, named colors and modern libadwaita CSS variables |

Your panel layout, authentication backend and application data are retained.

## Application integration

- **KDE standard apps and Haruna:** system palette, icons, supported Qt styling and glass window frames. Video remains opaque and sharp.
- **Firefox:** reversible chrome stylesheet in existing native/Flatpak profiles. Web pages, passwords and URL/certificate indicators remain intact.
- **Discord:** an active Vencord patch is detected; the official loader is added if approved, and the theme is activated through local Quick CSS. The official Flatpak patcher may add a narrow permission for its distribution directory; newly added grants are recorded for removal.
- **Steam:** a real Millennium skin is installed and selected. Native Steam uses the system loader runtime. Flatpak Steam uses its private persistent Steam directory, relative loader links and a local desktop-entry environment argument, with no broad filesystem permission.
- **TeamSpeak 3:** Qt's -stylesheet argument selects the theme through a local desktop entry. Its settings database is not rewritten.
- **ProtonPlus:** actual GTK4/libadwaita styling, including its existing Flatpak profile, plus matching icons and window presentation.

Vencord and Millennium are third-party extensions, not built-in Discord/Steam features. Future client updates can affect their compatibility. Independently drawn interfaces cannot all become identical to Apple's applications; the supported surfaces, controls, palette and icons are coordinated.

## KWin upgrades and recovery

The startup guard compares the running compositor with the version used to build the effect. After a mismatch or interrupted initial load, it retains native blur instead of loading an incompatible binary. Rerun install.sh after a KWin 6.8 update. Other Plasma versions are explicitly rejected.

    python3 package/tools/full_install.py status

A failed installation is not marked complete. Journals remain available for retry or removal. The installer does not add community repositories, change Steam's update channel, delete profiles or weaken lock-screen authentication.

## Validation and licenses

See [VALIDATION.md](package/VALIDATION.md) for automated restoration checks, native QtQuick/cursor rendering and OpenGL ES shader compilation. A full native C++ build on openSUSE could not be verified here because its package repositories were inaccessible. The installer builds on the target machine and reports failures. Actual Steam/Discord sessions, the Flatpak loader bridge and the SDDM authentication backend were not exercised here.

Original artwork/scripts: MIT. Bundled sources retain their licenses and copyright notices; see [THIRD_PARTY_NOTICES.md](package/THIRD_PARTY_NOTICES.md) and [vendor/](package/vendor/). Application/distribution marks retain their owners' rights.

German instructions: [ANLEITUNG.md](package/ANLEITUNG.md).

## Development checks

    python3 -m unittest discover -s tests -v

These tests use isolated temporary profiles and do not apply the theme to your desktop. Root-level shell scripts forward to the installers inside `package/`. The downloadable ZIP is a standalone package; inside it, use `python3 tools/full_install.py status`.
