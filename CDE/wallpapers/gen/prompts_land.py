"""Large photographic landscapes with a light CDE palette colour grade."""
import json
STYLE = ("Breathtaking landscape photograph, shot on a medium format camera with a wide lens, natural light, deep depth of field, crisp detail, "
         "subtle film-like colour grading, calm composition with open sky for desktop icons. ")
END = " No people, no buildings in the foreground, no text, no logos, no watermark."
L = {
 "alpen": dict(palette="Alpine", scene="High Alpine peaks with a sharp pyramid-shaped summit and glaciers at first light, a still mountain lake in the foreground mirroring the peaks, larch trees at the lake shore.",
     light="Early morning, pale sky blue and lavender sky, the summit glowing warm, cool blue shadows in the valley.",
     dark="Night under a clear starry sky, moonlight on the snowfields, the lake reflecting the stars, deep blue darkness."),
 "dolomiten": dict(palette="Desert", scene="Jagged pale limestone towers of the Dolomites rising above green alpine meadows, a winding gravel path, soft clouds around the peaks.",
     light="Golden evening light, the rock faces glowing in warm sand and rose tones, soft blue-grey shadows.",
     dark="Blue hour after sunset turning to night, the rock towers in deep shadow with a last faint rosy glow at the very top, first stars."),
 "fjord": dict(palette="NorthernSky", scene="A deep Norwegian fjord between steep dark mountain walls, a thin waterfall, the calm water stretching into the distance.",
     light="Overcast bright arctic daylight, cool petrol blue water, mist on the mountain tops.",
     dark="Polar night, a faint green and mauve aurora above the fjord reflected in the black water."),
 "toskana": dict(palette="Wheat", scene="Rolling Tuscan hills with golden wheat fields, a winding cypress-lined road, soft morning mist in the valleys.",
     light="Warm morning sun, golden wheat and pale blue sky, gentle haze.",
     dark="Moonlit night over the hills, silvery fields, dark cypress silhouettes, a deep blue sky with stars."),
 "watt": dict(palette="SeaFoam", scene="The Wadden Sea at low tide, wide shimmering mudflats with winding water channels and rippled sand reaching to a low horizon.",
     light="Soft bright sea light, pale sea-foam green and silver tones, wide airy sky.",
     dark="Dusk turning to night, the channels reflecting the last light, a deep blue-grey sky, one faint lighthouse beam far away on the horizon."),
 "island": dict(palette="Charcoal", scene="A black sand beach in Iceland with tall hexagonal basalt columns and sea stacks, gentle surf washing over the dark sand.",
     light="Moody overcast daylight, charcoal and slate tones, white surf.",
     dark="Night, the basalt columns barely visible, the surf glowing faintly under a cloudy moonlit sky."),
 "schwarzwald": dict(palette="Grass", scene="A dense Black Forest valley of tall fir trees with layers of morning fog between the ridges, a small meadow in the foreground.",
     light="Soft morning light breaking through the fog, deep greens and pale grey mist.",
     dark="Night in the forest valley, moonlit fog between dark fir silhouettes, very calm."),
 "elbsandstein": dict(palette="Sand", scene="Weathered sandstone pillars and table mountains of Saxon Switzerland rising above a sea of autumn forest and morning fog, the river valley below.",
     light="Sunrise, warm sandstone glowing above the fog, soft pastel sky.",
     dark="Night, the sandstone pillars as dark silhouettes above moonlit fog, stars above."),
}
def prompt(k, mode="hell"):
    d = L[k]; return STYLE + d["scene"] + " " + (d["light"] if mode == "hell" else d["dark"]) + END
if __name__ == "__main__":
    import sys
    seeds = [int(s) for s in sys.argv[1].split(",")]
    print(json.dumps([{"name": f"land_{k}_hell_{s}", "prompt": prompt(k), "seed": s} for k in L for s in seeds]))
