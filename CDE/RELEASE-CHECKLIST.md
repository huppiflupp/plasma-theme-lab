# Release-Checkliste CDE Copper

Vor jeder neuen Versionsnummer abarbeiten. Was nicht geprüft wurde, steht im
Commit als „nicht geprüft“ – nicht stillschweigend weglassen. TESTING.md bleibt
das Protokoll; diese Liste ist der Prüfplan.

## Immer (jede Version)

- [ ] `python3 build.py` ohne Fehler, `python3 tests/verify.py` grün
- [ ] `msgfmt --check --statistics -o /dev/null po/de.po`: 0 ungenau, 0 unübersetzt
- [ ] `python3 manage.py check` auf dem Testsystem: Ausgabe plausibel
- [ ] In der VM `plasma-lab` (Fedora, Plasma 6.7) installiert, Plasma neu gestartet:
      `journalctl --user -u plasma-plasmashell` ohne neue QML-Fehler/-Warnungen
      aus `org.cde.copper.*`
- [ ] Bildschirmfoto der Konsole angesehen (`vm/vmctl.sh shot`): alle Kacheln da,
      nichts abgeschnitten, kein leerer Platz
- [ ] Geänderte Funktion von Hand ausgelöst (Klick, Tastatur, Popup schließt mit Esc)
- [ ] Keine privaten Namen/Adressen im Produkt (Test `test_no_private_hosts_in_product`)
- [ ] Version in `build.py`/`po/README.md` erhöht, README und TESTING.md nachgezogen

## Bei Änderungen an der Konsole (frontpanel/)

- [ ] Konsole unten, oben, links, rechts (senkrecht!) angesehen
- [ ] Konsolengröße 1,0 und 1,5; Kontrast „hart“ ein/aus
- [ ] Eine helle und eine dunkle Palette (z. B. Copper und Graphite/Black)
- [ ] Einstellungsdialog öffnen, eine Option ändern, OK – Wert kommt an

## Bei Änderungen an Paletten, Symbolen, Stil (palettes/, icons.py, kvantum.py)

- [ ] `screenshots/icon-sheet-*.png` neu erzeugt und angesehen
- [ ] Symbole 16, 22 und skalierbar auf heller und dunkler Fläche erkennbar
- [ ] Ein Qt-Dialog (Dolphin „Öffnen“) und ein GTK-Programm angesehen

## Vor einer Store-Veröffentlichung zusätzlich

- [ ] Ubuntu-VM `ubuntu-lab` (Plasma 6.6): install, apply, uninstall
- [ ] Deinstallation stellt die Konfiguration wieder her (Test + Augenschein)
- [ ] README-Screenshots entsprechen dem aktuellen Standard (z. B. Starter „Layouts“)
- [ ] Offene Punkte aus REVIEW-*.md durchgesehen

## Bekannt ungeprüft (bis jemand es tut)

- X11-Sitzung
- Zwei physische Bildschirme („eine Konsole je Bildschirm“)
- Screenreader; Tastaturbedienung von Anwendungsmenü und Auto-Hide
