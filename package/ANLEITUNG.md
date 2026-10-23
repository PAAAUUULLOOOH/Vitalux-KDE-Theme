# Liquid Glass für openSUSE

Theme-Paket für **openSUSE Tumbleweed, Plasma/KWin 6.8.x, Wayland und x86_64**. Enthalten sind globales Design, shaderbasierte Glasbrechung, Qt-/GTK-Styles, Fensterrahmen, Cursor, Icons, 4K-Hintergrund, Startanimation, SDDM-Design und App-Anpassungen.

## Installieren

ZIP vollständig entpacken, Discord und Steam schließen und ein Terminal im entpackten Ordner öffnen. Ohne sudo starten:

    bash install.sh

Der Installer prüft das Paket, installiert Build-Pakete aus deinen eingerichteten openSUSE-Quellen und baut den Glaseffekt passend zu deiner KWin-Version. Für Systemdateien fragt er gezielt nach dem sudo-Passwort. Internetzugang wird für Abhängigkeiten und fehlende App-Erweiterungen benötigt.

Wenn Discord/Steam noch keinen Theme-Loader haben, werden Vencord bzw. Millennium vorab erklärt und erst nach deiner Bestätigung eingerichtet. Offizielle Release-Downloads werden per SHA-256 geprüft. Vorhandene Loader werden übernommen; normale/Flatpak-Installationen werden erkannt.

Danach einmal ab- und wieder anmelden. Es werden keine Programme zwangsweise beendet und kein Displaymanager neu gestartet.

    # Prüfen, ohne Einstellungen zu ändern:
    bash install.sh --check

    # Firefox-Oberfläche unverändert lassen:
    bash install.sh --no-firefox

## Entfernen

    bash uninstall.sh

Die vorherigen Einstellungen und Dateien werden wiederhergestellt. Programme, Konten, Spiele, Passwörter und Browserdaten bleiben erhalten. Spätere eigene Änderungen werden beibehalten. Vorher vorhandene Loader bleiben bestehen; nur durch diesen Installer ergänzte Loader werden zurückgenommen. Steam-Dateien/Symlinks und neu ergänzte Vencord-Freigaben sind berücksichtigt.

Sicherungen liegen in ~/.local/state/liquid-glass-kde und /var/lib/liquid-glass-kde. Über zypper installierte Build-Pakete bleiben aus Rücksicht auf andere Programme installiert.

## Anpassungen

- **Plasma:** Glasflächen mit Brechung und Lichtkanten, blaue Akzente und Fensterrahmen.
- **openSUSE-Startmenü:** Das installierte Originalsymbol wird übernommen und auf einer Glasfläche dargestellt.
- **Standard-Apps und Haruna:** Systemfarben, unterstützte Qt-Steuerelemente, Fensterrahmen und Icons. Videos bleiben deckend und scharf.
- **Cursor:** mehrere Größen bis 96 px und animierte Wartezeiger.
- **Start/Sperre/Login:** animierte Startansicht; Sperrhintergrund und Systempalette; eigenes Anmeldedesign bei installiertem SDDM. Die native Passwortprüfung bleibt erhalten.
- **Firefox:** zurücknehmbare Oberfläche in bestehenden nativen/Flatpak-Profilen; Webseiten und Sicherheitsanzeigen bleiben erhalten.
- **Discord:** Vencord Quick CSS wird eingerichtet und aktiviert. Der offizielle Installer kann bei Flatpak eine begrenzte Freigabe für seinen eigenen Ordner ergänzen; diese wird zur Rücknahme erfasst.
- **Steam:** Millennium-Skin wird installiert und ausgewählt. Bei Flatpak liegen die Loader-Dateien im eigenen Steam-Verzeichnis; der lokale Starter erhält das passende Argument. Keine allgemeine Home-Freigabe.
- **TeamSpeak 3:** Stylesheet wird über den Starter geladen. Die Einstellungsdatenbank bleibt erhalten.
- **ProtonPlus/GTK4:** tatsächliches GTK4-/Libadwaita-Styling, auch im bestehenden ProtonPlus-Flatpak-Profil.

Vencord und Millennium sind zusätzliche Erweiterungen. Zukünftige Steam-/Discord-Updates können deren Anpassung beeinflussen. Die Darstellung ist eine KDE-Adaption; Apples Betriebssystem und dessen Optik werden nicht vollständig kopiert.

## Nach einem KWin-Update

Der Glaseffekt wird nur bei passender laufender KWin-Version geladen. Bei einer Abweichung bleibt der native Blur aktiv. Nach einem Update innerhalb von 6.8.x install.sh erneut ausführen. Andere Plasma-Versionen werden nicht ungeprüft akzeptiert.

    python3 tools/full_install.py status

Bei einem Fehler wird keine vollständige Installation gemeldet. Sicherungen bleiben zur Wiederholung/Deinstallation erhalten. Es werden keine Community-Repositories angelegt und keine Profile gelöscht.

Prüfungen stehen in VALIDATION.md. Ein vollständiger Build auf openSUSE war hier wegen gesperrter Paketserver nicht möglich; er erfolgt im Installer auf deinem Rechner. Echte Steam-/Discord-Sitzungen, die Flatpak-Loader-Brücke und die SDDM-Anmeldung konnten hier nicht geprüft werden.

Quellen/Lizenzen: THIRD_PARTY_NOTICES.md, LICENSE und vendor/.
