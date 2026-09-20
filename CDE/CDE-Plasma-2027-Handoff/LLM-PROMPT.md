# Auftrag an das Coding-LLM

Du erhältst ein vollständiges Design-Handoff für ein KDE-Plasma-6-Theme namens **CDE Plasma 2027**. Lies zuerst `README.md`, `MANIFEST.md`, `DESIGN-SPEC.md`, `KDE-PLASMA-MAPPING.md`, `IMPLEMENTATION-GUIDE.md` und `design-tokens.json`. Analysiere anschließend alle Bilder in `references/`.

## Ziel

Baue einen installierbaren, reversiblen Prototypen für KDE Plasma 6, der wie eine moderne Weiterentwicklung von CDE/Motif wirkt. Die verbindliche Bildreferenz ist `references/05-target-teal-copper-panel.png`. Die übrigen Bilder dokumentieren Entwurfsstufen und dürfen nicht ungeprüft gemischt werden.

## Unverhandelbare Anforderungen

1. Petrol/Türkis und Kupferorange gemäß den Design-Tokens.
2. Harte, mehrstufige Motif-Bevels; praktisch keine Rundungen.
3. Keine erkennbare Breeze-, Oxygen-, Material- oder „KDE-Plastik“-Ästhetik.
4. Eigenständige Workstation-Icons; keine Standardicons im sichtbaren Kernbereich.
5. Schwebendes, zweistöckiges Frontpanel mit mechanisch wirkenden Segmenten und kleinen Subpanel-Auslösern.
6. Panelmodi: sichtbar, automatisch ausblenden, Hotspot/Griffkante.
7. Plasma 6, Qt 6, HiDPI und Wayland; keine Root-Pflicht.
8. Installation und Deinstallation dürfen keine fremden Dateien überschreiben oder löschen.

## Vorgehen

Arbeite in überprüfbaren Phasen. Beginne ausschließlich mit Phase 1 aus `IMPLEMENTATION-GUIDE.md`. Lege vor dem Schreiben eine kurze Komponenten- und Dateistruktur vor. Implementiere danach vollständige Dateien, keine isolierten Fragmente. Führe Syntax-/QML-Prüfungen aus, starte soweit möglich einen isolierten Plasma-Test und dokumentiere verbleibende Einschränkungen.

Erzeuge nach Phase 1:

- installierbares Farbschema
- Fensterdekorations-Prototyp
- statisches zweistöckiges Frontpanel
- zwölf Kernicons
- `install.sh`, `uninstall.sh` und eigenes Installationsmanifest
- README mit Voraussetzungen und Testschritten
- Screenshots bei 1920×1080 und, falls verfügbar, 2560×1440

## Entscheidungspflichten

Wenn Plasma-APIs oder Distributiondetails fehlen, halte an der kleinsten notwendigen Stelle an und frage gezielt nach Plasma-Version und Distribution. Erfinde keine API. Wenn zwei normale Plasma-Panels für den ersten Prototyp verwendet werden, kennzeichne dies ausdrücklich als Phase-1-Näherung und plane das gemeinsame QML-Containment als Zielarchitektur.

## Selbstprüfung vor Übergabe

Vergleiche den Prototyp mit der Zielreferenz und beantworte:

- Ist CDE/Motif ohne Erläuterung erkennbar?
- Ist das Panel ein eigenständiges Frontpanel oder nur eine eingefärbte Taskbar?
- Sind Kupferflächen sparsam und funktional eingesetzt?
- Gibt es sichtbare Standardicons oder moderne Rundungen?
- Sind aktive, inaktive, Hover-, Fokus- und gedrückte Zustände eindeutig?
- Funktionieren Installation, Deinstallation, Tastaturbedienung und HiDPI?

Behebe gefundene P0/P1-Abweichungen vor der Übergabe.
