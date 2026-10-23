# Vitalux Liquid Silver für KDE

Für **openSUSE Tumbleweed, Plasma/KWin 6.8.x, Wayland und x86_64**. Vorlage ist das originale **Liquid Silver** aus Vitalux: dunkles Rauchglas, Silberfarben, Lichtkanten und der originale Hintergrund. Die Farben und Materialwerte sind aus dem Vitalux-Code übernommen; das verlustfreie 4K-Referenzbild stimmt Pixel für Pixel mit dessen Zeichenfunktion überein.

## Installieren

ZIP vollständig entpacken, Discord und Steam schließen und im entpackten Ordner ein Terminal öffnen:

```bash
bash install.sh
```

Ohne vorangestelltes sudo starten. Der Installer prüft die ZIP-Inhalte, sichert die bisherigen Einstellungen, installiert benötigte Build-Pakete aus deinen openSUSE-Quellen und baut den Glaseffekt passend zu KWin. Für Systemdateien fragt er nach dem sudo-Passwort. Internet wird benötigt. Fehlende Discord-/Steam-Loader (Vencord/Millennium) werden vorab erklärt und benötigen deine Bestätigung.

Danach einmal ab- und wieder anmelden. Es werden keine Programme zwangsweise beendet.

```bash
bash install.sh --check       # Nur prüfen
bash install.sh --no-firefox  # Firefox-Oberfläche beibehalten
bash uninstall.sh            # Ursprünglichen Zustand wiederherstellen
```

Beim Wechsel von 1.0.0 einfach den neuen Installer ausführen. Die erste Sicherung bleibt erhalten. Bewahre den entpackten Ordner für die Deinstallation auf.

## Enthalten

Plasma-Oberflächen, Qt-/GTK3-/GTK4-Steuerelemente, Glasrahmen, Cursor, Originalhintergrund, Startanimation und SDDM-Anmeldedesign. Das installierte openSUSE-Originalsymbol und vorhandene App-Logos werden auf dunkle Glasflächen gesetzt. Firefox, Discord, Steam, TeamSpeak 3, ProtonPlus und Haruna erhalten die passenden unterstützten Farben und Oberflächen. Videos, Webseiten und Sicherheitsanzeigen bleiben unverändert. Die Apps behalten ihren eigenen Aufbau.

Die Vorschaubilder zeigen echte QtQuick-Darstellungen einzelner Komponenten, keine vollständige KDE-Sitzung. Dort ist ein Vorschaumotiv zu sehen; bei der Installation wird das installierte openSUSE-Originalsymbol verwendet.

## Rücknahme und Updates

Die Deinstallation stellt gesicherte Dateien/Einstellungen wieder her, berücksichtigt spätere eigene Änderungen und entfernt nur selbst ergänzte App-Loader. Profile, Konten, Spiele und Browserdaten bleiben erhalten. Sicherungen: `~/.local/state/liquid-glass-kde` und `/var/lib/liquid-glass-kde`. Build-Pakete bleiben installiert.

Nach einem KWin-Update bleibt bei unpassender Effekt-Version der native Blur aktiv. Innerhalb 6.8.x den Installer erneut ausführen.

```bash
python3 tools/full_install.py status
```

Ein vollständiger Build und eine echte KDE-/Steam-/Discord-/SDDM-Sitzung konnten hier nicht geprüft werden. Tests und Grenzen: VALIDATION.md. Original-Vitalux-Material bleibt unter dessen bisherigem Lizenzhinweis; weitere Lizenzen stehen in LICENSE-NOTICE.md und THIRD_PARTY_NOTICES.md.
