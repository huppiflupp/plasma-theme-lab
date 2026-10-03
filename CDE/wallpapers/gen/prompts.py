import json
STYLE = ("Abstract digital desktop wallpaper in the style of the KDE Plasma 5 default wallpapers: a stylised low-poly 3D world, every surface "
         "built from subtly shaded triangular facets and flat hexagonal tiles, clean crisp geometric edges, soft ambient light, gentle glow along "
         "highlighted borders, smooth colour gradients across the facets, calm and polished, plenty of quiet space. ")
LIGHT = ("Colour palette: misty pale teal-grey, sea-glass green-grey, muted slate teal and deep petrol teal, with glowing warm copper "
         "and peach orange accents. Bright daylight, airy. ")
DARK = ("Colour palette: very dark night petrol teal close to black, dark slate blue-green and charcoal, muted teal facets, with glowing warm copper "
        "and amber orange accents. Night scene, low overall brightness, dark background. ")
END = "No text, no logos, no letters, no watermark, no people, no animals."
MOTIVE = {
 "canopee": "Seen from above at an angle, a broad smooth ribbon road curves in a large sweeping arc across a gently rolling landscape of hexagonal tiles, the ribbon edged on both sides by a thin glowing copper border, the tiled ground fades into soft triangulated facets towards the edges.",
 "altai": "Low-poly faceted mountain range made of large flat triangles, sharp peaks with pale snow facets catching warm light from a low glowing sun behind the summit, the mountains mirrored in a perfectly still lake in the lower third.",
 "cluster": "A smooth flat gradient surface on the left that breaks up towards the right into a loose cluster of hexagonal tiles drifting apart, through the gaps between the tiles a deep space nebula with soft glowing gas and tiny stars shows through.",
 "fluss": "Viewed straight from above, a flat honeycomb floor of hexagonal tiles in muted slate tones, a winding river of brightly coloured hexagons meanders from the top left corner to the bottom right corner, its colour shifting gradually from pale teal through teal to glowing copper orange, a few lone tiles slightly lighter scattered around.",
 "kaskade": "A glacier of pale translucent faceted ice sheets cascades down over stepped terraces of hexagonal tiles, the terraces bordered by thin glowing copper edges, a narrow stream of light teal water winds along the side, seen from above at an angle.",
}
def prompt(m, mode): return STYLE + MOTIVE[m] + " " + (LIGHT if mode == "hell" else DARK) + END
if __name__ == "__main__":
    import sys
    seeds = [int(s) for s in sys.argv[1].split(",")]
    modes = sys.argv[2].split(",")
    jobs = [{"name": f"{m}_{mode}_{s}", "prompt": prompt(m, mode), "seed": s} for m in (sys.argv[3].split(",") if len(sys.argv) > 3 else MOTIVE) for mode in modes for s in seeds]
    print(json.dumps(jobs, indent=1))
