// Sayings for the compact box's bottom line.
//
// The originals are public domain (Laozi, Confucius, Heraclitus, Seneca,
// Epictetus, Marcus Aurelius); the German and English wordings are our own
// renderings, not quoted from any modern translation, so they fall under the
// theme's licence. The last few lines are the theme's own. Kept short: the
// box is about 150 px wide and shows four lines at most.
.pragma library

const SAYINGS = [
    {by: "Laozi", de: "Eine Reise von tausend Meilen beginnt unter deinen Füßen.", en: "A journey of a thousand miles begins beneath your feet."},
    {by: "Laozi", de: "Wer andere kennt, ist klug. Wer sich selbst kennt, ist weise.", en: "Who knows others is clever. Who knows himself is wise."},
    {by: "Laozi", de: "Wer weiß, dass er genug hat, ist reich.", en: "Who knows he has enough is rich."},
    {by: "Laozi", de: "Das höchste Gute ist wie das Wasser.", en: "The highest good is like water."},
    {by: "Laozi", de: "Nichts ist weicher als Wasser, doch nichts bezwingt das Harte besser.", en: "Nothing is softer than water, yet nothing overcomes the hard better."},
    {by: "Laozi", de: "Tu das Schwere, solange es leicht ist, das Große, solange es klein ist.", en: "Do the hard while it is easy, the great while it is small."},
    {by: "Laozi", de: "Dreißig Speichen teilen eine Nabe; das Leere in ihr macht das Rad.", en: "Thirty spokes share one hub; the emptiness in it makes the wheel."},
    {by: "Laozi", de: "Wer weiß, redet nicht. Wer redet, weiß nicht.", en: "Those who know do not talk. Those who talk do not know."},
    {by: "Konfuzius", byEn: "Confucius", de: "Wissen, was man weiß, und wissen, was man nicht weiß: das ist Wissen.", en: "To know what you know and know what you do not: that is knowledge."},
    {by: "Konfuzius", byEn: "Confucius", de: "Einen Fehler machen und ihn nicht berichtigen: das erst ist ein Fehler.", en: "To err and not to mend it: that is the error."},
    {by: "Heraklit", byEn: "Heraclitus", de: "Man steigt nicht zweimal in denselben Fluss.", en: "You cannot step twice into the same river."},
    {by: "Seneca", de: "Nicht weil es schwer ist, wagen wir es nicht; weil wir es nicht wagen, ist es schwer.", en: "It is not because things are hard that we do not dare; they are hard because we do not dare."},
    {by: "Seneca", de: "Alles andere ist fremd; nur die Zeit gehört uns.", en: "All else is another's; time alone is ours."},
    {by: "Seneca", de: "Während wir aufschieben, eilt das Leben vorbei.", en: "While we put it off, life runs past."},
    {by: "Seneca", de: "Wer überall ist, ist nirgends.", en: "Who is everywhere is nowhere."},
    {by: "Seneca", de: "Wer lehrt, lernt.", en: "We learn by teaching."},
    {by: "Seneca", de: "Wer seinen Hafen nicht kennt, dem ist kein Wind der rechte.", en: "No wind is fair for one who knows not his harbour."},
    {by: "Seneca", de: "Vieles erschreckt uns mehr, als es uns bedrängt.", en: "More things frighten us than harm us."},
    {by: "Seneca", de: "Das Leben ist lang, wenn man es zu nutzen weiß.", en: "Life is long if you know how to use it."},
    {by: "Seneca", de: "Das beste Mittel gegen den Zorn ist Aufschub.", en: "The best cure for anger is delay."},
    {by: "Epiktet", byEn: "Epictetus", de: "Nicht die Dinge beunruhigen uns, sondern unsere Meinungen über sie.", en: "It is not things that trouble us, but our opinions of them."},
    {by: "Marc Aurel", byEn: "Marcus Aurelius", de: "Die Welt ist Wandel, das Leben Auffassung.", en: "The world is change, life is opinion."},
    {by: "Marc Aurel", byEn: "Marcus Aurelius", de: "Die beste Art, sich zu wehren: nicht so zu werden wie der andere.", en: "The best defence is not to become like the other."},
    {by: "Marc Aurel", byEn: "Marcus Aurelius", de: "Nicht mehr reden, wie ein guter Mensch sein soll – einer sein.", en: "No more talk of what a good man should be. Be one."},
    {by: "Marc Aurel", byEn: "Marcus Aurelius", de: "Grabe nach innen. Innen ist die Quelle des Guten.", en: "Dig within. Within is the spring of the good."},
    {by: "Marc Aurel", byEn: "Marcus Aurelius", de: "Die Seele nimmt die Farbe ihrer Gedanken an.", en: "The soul takes on the colour of its thoughts."},
    {by: "Warp Legacy", de: "Auch ein Neustart ist ein Anfang.", en: "A reboot, too, is a beginning."},
    {by: "Warp Legacy", de: "Ein leerer Schreibtisch ist ein offener.", en: "An empty desktop is an open one."},
    {by: "Warp Legacy", de: "Erst sichern, dann staunen.", en: "Back up first, then marvel."}
];

// The saying for a slot of time: a stride through the list (coprime to its
// length) so neighbours in the list do not follow each other.
function at(slot, german) {
    const n = SAYINGS.length;
    const i = ((slot * 7) % n + n) % n;
    const s = SAYINGS[i];
    return {text: german ? s.de : s.en, by: german ? s.by : (s.byEn || s.by)};
}
