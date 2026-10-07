"""Seamless material tiles: flat, even, top-down, no focal point."""
import json
STYLE = ("Seamless texture, a top-down orthographic macro photograph of a flat surface filling the entire frame edge to edge, perfectly even soft diffuse lighting, "
         "no vignette, no shadows from objects, uniform density everywhere, no focal point, no horizon, no edges or borders, high detail. ")
END = " No text, no logos, no objects, no people."
T = {
 "flokati": "A thick white Greek flokati shag rug, long curly tufts of soft wool fibres densely packed, fluffy and cosy.",
 "moos": "A dense carpet of fresh green cushion moss, tiny star-shaped leaves and soft round clumps, slightly moist.",
 "filz": "Thick grey wool felt, matted soft fibres with tiny flecks, a few loose fibres on the surface.",
 "kork": "A natural cork board, pressed granulated cork pieces in warm tan and brown tones.",
 "terrazzo": "Polished terrazzo floor, small chips of marble in grey, white, rust and green set in a pale cement matrix.",
 "leinen": "Natural undyed linen fabric, visible irregular slub weave, soft creases flattened, oatmeal colour.",
 "buettenpapier": "Handmade cotton paper, visible fibres and tiny inclusions, soft uneven deckled texture, off-white.",
 "sand": "Fine pale sand raked into parallel gently wavy lines like a Japanese zen garden, soft grain visible.",
 "schiefer": "A natural cleft slate surface, layered dark grey stone with subtle rust and blue tints, fine ridges.",
 "travertin": "Honed travertine stone, warm cream with darker veins and small natural holes.",
 "rattan": "Tightly woven natural rattan cane webbing in an open octagonal pattern, light honey colour.",
 "velours": "Plush velvet fabric with a soft sheen, crushed pile catching the light in subtle waves, deep colour.",
 "strick": "Chunky hand knitted wool in a cable knit pattern, thick soft yarn, cream colour.",
 "lava": "Porous volcanic lava stone, dark grey-black with many small irregular holes and rough rusty brown specks.",
 "kies": "Small rounded river pebbles and gravel in grey, beige and slate tones, densely packed.",
 "wasser": "Clear shallow water over pale sand seen from above, shimmering caustic light patterns, gentle ripples.",
 "eisblumen": "Frost flowers, delicate feathery ice crystals grown on a window pane, white on dark blue-grey.",
 "akustikschaum": "Charcoal acoustic foam panels with a regular pattern of small pyramids, soft porous foam texture.",
 "leder": "Smooth full-grain leather with a fine natural pebble grain, soft sheen, cognac brown.",
}
def prompt(k): return STYLE + T[k] + END
if __name__ == "__main__":
    import sys
    seeds = [int(s) for s in sys.argv[1].split(",")]
    print(json.dumps([{"name": f"tile_{k}_{s}", "prompt": prompt(k), "seed": s, "w": 1024, "h": 1024} for k in T for s in seeds]))
