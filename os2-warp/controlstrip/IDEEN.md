# Kompakter Kasten: was nützlicher wäre (Vorschlag, 21.10.2026)

Der Kasten oben rechts (Layout „compact“) hat drei Bereiche. Heute zeigt
oben nur die Marke, unten nur ein festes Motto; beides sieht gut aus, tut
aber nichts. Bewertung: **N** Nutzen, **A** Aufwand, **D** Datenschutz/Netz.

## Oben (Marke)

| Idee | N | A | D | Urteil |
|---|---|---|---|---|
| **Nächste Termine** (Plasma-Kalender-Plugins: KOrganizer/Akonadi, Feiertage, Mondphasen) – zwei Einträge der nächsten 14 Tage; **gibt es keine, steht die Marke da** | hoch | mittel | lokal | **umgesetzt, Vorgabe** |
| Marke wie bisher | gering | – | – | bleibt als Option |
| **Wetter** (wttr.in, Ort frei wählbar, ohne Schlüssel), Klick öffnet die Vorhersage im Browser | mittel | mittel | Netz, IP sichtbar | **umgesetzt, Vorgabe AUS** |
| Klick auf die Marke öffnet das Warp-Menü | mittel | hoch | – | weggelassen: das Menü kaskadiert nach rechts und ist für eine Leiste oben gebaut; am rechten Rand liefe es aus dem Bild |

## Mitte (Uhr, Datum, Messwerte)

| Idee | N | A | D | Urteil |
|---|---|---|---|---|
| **Klick auf Uhr/Datum → Monatskalender mit Terminen** (Popup), darin „Kalender öffnen“; wahlweise direkt die Kalender-App (`@calendar`: Merkuro, KOrganizer, GNOME Kalender, Thunderbird) | hoch | mittel | lokal | **umgesetzt** |
| **Klick auf CPU/RAM/Kurve → Systemmonitor** (`@sysmon`: Plasma-Systemmonitor, KSysGuard, GNOME-Systemüberwachung …) | hoch | gering | lokal | **umgesetzt** |
| **Klick auf „/“ → Plattenbelegung** (`@diskusage`: Filelight, Baobab, QDirStat, sonst Dateiverwaltung in „/“) | mittel | gering | lokal | **umgesetzt** |
| Akku/Netz-Anzeige | mittel | mittel | lokal | weggelassen: zeigt die Systemleiste schon, und der Kasten würde höher |

## Unten (Motto)

| Idee | N | A | D | Urteil |
|---|---|---|---|---|
| **Sprüche, rotierend** (alle 15 min / stündlich / täglich), deutsch oder englisch nach Sprache; Klick zeigt den nächsten | mittel | gering | lokal | **umgesetzt, Vorgabe stündlich** |
| Festes Motto (bisher) | gering | – | – | bleibt als Option „fester Text“ |
| **News-Schlagzeilen** aus einem RSS/Atom-Feed per URL, rotierend, Klick öffnet den Artikel | mittel | mittel | Netz | **umgesetzt, Vorgabe AUS, keine Vorgabe-URL** |

Die Sprüche sind **eigene Übertragungen** gemeinfreier Originale (Laozi,
Konfuzius, Heraklit, Seneca, Epiktet, Marc Aurel) und ein paar eigene
Zeilen – keine modernen Übersetzungen, also kein fremdes Urheberrecht.

## Leitplanken

- Netzzugriffe (Wetter, News) nur, wenn der Nutzer sie einschaltet; Abruf
  alle 30 min (einstellbar, mindestens 15), Fehler still: dann bleibt die
  letzte Anzeige bzw. ein knapper Hinweis stehen.
- Keine API-Schlüssel, keine privaten Hosts als Vorgabe; die Einstellungsseite
  nennt die Quelle und dass sie die IP-Adresse sieht.
- Feste Höhe je Bereich, damit die Leiste nicht bei jedem Spruchwechsel springt.
