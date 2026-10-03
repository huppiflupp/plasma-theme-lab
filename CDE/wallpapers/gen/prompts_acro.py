"""Late-1990s software box editorial illustration style (homage, no branding)."""
import json
STYLE = ("A late 1990s editorial illustration as seen on software box covers: loose expressive black ink outlines, gouache and coloured pencil "
         "with visible brush strokes and cross-hatching, bold saturated colours dominated by cobalt and sky blue, sunny yellow and warm red, "
         "energetic swooping motion arcs, slightly exaggerated cartoonish proportions, a hand-painted and optimistic look. ")
END = " Full-bleed illustration, no text, no letters, no logos, no brand names, no watermark."
STYLE2 = ("A late 1990s editorial illustration as printed on a software box: a fine, loose black ink line drawing with delicate coloured pencil "
          "cross-hatching over soft transparent watercolour washes, an airy light palette of pale sky blue, cobalt accents, butter yellow and small touches "
          "of warm red, lots of white paper showing through, gentle swooping motion arcs, elegant and calm rather than cartoonish. ")
M = {
 "datenflug": "A cheerful leaping technician in a yellow shirt with a flying red tie and dark trousers jumps joyfully across the frame, tossing floating windows, floppy disks and paper documents along a big curved arrow arc towards a small blue globe, below him a wavy green and ochre landscape with a winding river and a tiny colourful city skyline, swirling blue sky with brushy clouds.",
 "netzwerk": "Envelopes, floppy disks, paper pages and a small beige computer monitor fly along a huge sweeping translucent arrow arc from the left over rolling wavy hills to a glowing globe on the right, a tiny colourful city skyline on the horizon, swirling painterly blue sky, no people.",
 "workstation": "A big stylised 1990s computer workstation with a chunky monitor stands on wavy hills, from its screen a whirlwind of overlapping windows, charts and paper documents bursts out and spirals up into a swirling blue sky towards a small globe, painterly clouds, a tiny city skyline far away, no people.",
 "panorama": "A wide calm panorama of wavy rolling hills in green, ochre and blue with a winding river and a tiny colourful city skyline in the lower part of the frame, a large swirling painterly blue sky with brushy clouds fills the upper two thirds, a single small paper airplane trails a curved dotted line across the sky, no people.",
}
M2 = {
 "netzwerk": "Envelopes, floppy disks, paper pages and a small beige computer monitor drift along a long sweeping translucent arrow arc that rises from the lower middle and curves to a small globe at the upper right, below a thin band of softly wavy hills with a tiny city skyline on the horizon, the left half of the picture is open pale sky with a few light pencil clouds, no people.",
 "workstation": "A stylised 1990s computer workstation with a chunky monitor stands on a gentle wavy hill on the right side, from its screen a light ribbon of overlapping windows, small charts and paper pages spirals up and away towards a small globe, the left half of the picture is calm open pale sky with a few pencil-hatched clouds and a distant tiny city skyline, no people.",
}
def prompt(m, v=1): return (STYLE + M[m] if v == 1 else STYLE2 + M2[m]) + END
if __name__ == "__main__":
    import sys
    seeds = [int(s) for s in sys.argv[1].split(",")]
    print(json.dumps([{"name": f"acro_{m}_{s}", "prompt": prompt(m), "seed": s, "w": 1024, "h": 576, "front": True} for m in M for s in seeds]))
