// nt-legacy-win98 - Panelvorgabe

// Ein Panel je Bildschirm.
//
// Bis 0.2.14 legte dieses Skript genau EINES an - so wie Plasmas eigene
// Vorlage (layout-templates/org.kde.plasma.desktop.defaultPanel). Auf
// einem Rechner mit einem Bildschirm ist das richtig. Auf zweien nicht:
// Plasma entscheidet dann selbst, auf welchem das eine Panel landet, und
// auf dem anderen ist keine Taskleiste. Gemeldet als "wenn ich auf NT
// Legacy zurueckschalte, kommt keine Taskleiste mehr" - und weil die
// Wahl von Lauf zu Lauf anders ausfallen kann, sah es aus, als laege es
// an der Variante.
//
// Nachgemessen auf einem Rechner mit zwei 2560er Schirmen: screenCount=2,
// panels().length=1, panel.screen=0.
var alle = panels();
for (var i = 0; i < alle.length; i++) {
    alle[i].remove();
}

for (var s = 0; s < screenCount; s++) {
    var panel = new Panel;
    panel.screen = s;
    panel.location = "bottom";
    panel.height = 30;
    panel.floating = false;
    panel.hiding = "none";
    panel.alignment = "left";

    // Das Anwendungsmenue, nicht der Anwendungsstarter.
    //
    // org.kde.plasma.kickoff ist Plasmas Vorgabe: ein Fenster mit
    // Suchfeld, Kachelraster und Reitern. org.kde.plasma.kicker ist das
    // aufklappende Menue mit Untermenues - das, was Windows 95 bis 2000
    // hatte, und das Einzige von beiden, das zu dieser Formensprache
    // passt. Es bringt ausserdem die Seitenleiste mit, die der
    // Plasma-Stil einfaerbt (widgets/frame, Praefix "plain").
    panel.addWidget("org.kde.plasma.kicker");
    panel.addWidget("org.kde.plasma.icontasks");
    panel.addWidget("org.kde.plasma.systemtray");
    panel.addWidget("org.kde.plasma.digitalclock");

    // Ab dem zweiten Bildschirm: nur behalten, wenn es dort auch
    // wirklich sitzt. setScreen geht ueber Corona::setScreenForContainment
    // und kann fehlschlagen - dann laegen alle Panels uebereinander auf
    // demselben Schirm, und das waere schlimmer als der Zustand vorher.
    // Das erste wird NIE entfernt: ein Panel weniger ist genau der
    // Fehler, den diese Datei beheben soll.
    if (s > 0 && panel.screen !== s) {
        panel.remove();
    }
}

// Hier stand bis 0.2.14 ein Block, der Laenge, Mindest- und Hoechstlaenge
// des Panels auf die Bildschirmbreite setzte - gegen ein Panel, das
// angeblich nur 34 Pixel breit wurde.
//
// Den gab es nie. "panel.length" liefert nicht die gezeichnete Breite,
// sondern die Breite des INHALTS; die Diagnose beruhte auf dieser
// Fehlablesung. In der Test-VM gemessen: ohne jede Laengenangabe steht
// lengthMode auf "fill", minimumLength und maximumLength stehen auf
// 1280 - und das Panel ist auf dem Bildschirmfoto ueber die volle Breite
// gezeichnet, waehrend "length" 388 meldet.
//
// Schaedlich war der Block obendrein: minimumLength und maximumLength
// auf denselben Wert zu setzen nagelt das Panel auf eine feste Groesse
// fest. Auf einem zweiten Bildschirm anderer Breite passt die dann
// nicht mehr, und der Rueckfallwert 99999 (fuer den Fall, dass
// screenGeometry noch nichts weiss) nagelt es auf eine Breite fest, die
// es nirgends gibt.
//
// Plasmas eigene Vorlage setzt die Laenge ebenfalls nicht.

var flaechen = desktops();
for (var j = 0; j < flaechen.length; j++) {
    flaechen[j].wallpaperPlugin = "org.kde.image";
    flaechen[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    flaechen[j].writeConfig("Image", "ntlegacy-win98");
    flaechen[j].reloadConfig();
}
