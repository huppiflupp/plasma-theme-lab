// The compact box's network sources, both off until the user turns them on:
// the weather from wttr.in (no key, the place is free text) and headlines
// from any RSS or Atom feed. Only parsing lives here; main.qml fetches.
.pragma library

// wttr.in's JSON (or that of a self-hosted wttr.in); an empty place lets
// the server guess it from the IP address. "" for a server that is no URL.
function weatherUrl(server, place, lang) {
    const base = String(server || "").trim().replace(/\/+$/, "");
    if (!/^https?:\/\/[^\s]+$/.test(base)) return "";
    return base + "/" + encodeURIComponent(String(place || "").trim()) + "?format=j1&lang=" + lang;
}
// The page a click opens: the same place, readable.
function weatherPage(server, place, lang) {
    const url = weatherUrl(server, place, lang);
    return url ? url.replace("format=j1&", "") : "";
}

// World Weather Online's condition codes (which wttr.in passes on) to
// freedesktop/Breeze weather icons.
function weatherIcon(code, night) {
    code = Number(code);
    if (code === 113) return night ? "weather-clear-night" : "weather-clear";
    if (code === 116) return night ? "weather-few-clouds-night" : "weather-few-clouds";
    if (code === 119) return "weather-clouds";
    if (code === 122) return "weather-overcast";
    if ([143, 248, 260].indexOf(code) >= 0) return "weather-fog";
    if ([200, 386, 389, 392, 395].indexOf(code) >= 0) return "weather-storm";
    if ([179, 182, 185, 281, 284, 311, 314, 317, 350, 362, 365, 374, 377].indexOf(code) >= 0) return "weather-freezing-rain";
    if ([227, 230, 323, 326, 329, 332, 335, 338, 368, 371].indexOf(code) >= 0) return "weather-snow";
    if ([176, 263, 266, 293, 296, 353].indexOf(code) >= 0) return "weather-showers-scattered";
    if ([299, 302, 305, 308, 356, 359].indexOf(code) >= 0) return "weather-showers";
    return "weather-none-available";
}

// {temp, text, icon, place} from wttr.in's j1 JSON, or null.
function parseWeather(json, lang, fahrenheit) {
    let data;
    try { data = JSON.parse(json); } catch (e) { return null; }
    const now = data && data.current_condition && data.current_condition[0];
    if (!now) return null;
    const local = now["lang_" + lang];
    const text = (local && local[0] && local[0].value) || (now.weatherDesc && now.weatherDesc[0] && now.weatherDesc[0].value) || "";
    const area = data.nearest_area && data.nearest_area[0];
    const place = (area && area.areaName && area.areaName[0] && area.areaName[0].value) || "";
    // The place's own time; wttr.in has stopped sending it at times, and the
    // empty text came out as hour 0: a moon over Austin in the afternoon
    // (VM, 21.10.2026). Without it, day.
    const clock = /(\d+):\d+ (AM|PM)$/.exec(String(now.localObsDateTime || ""));
    const hour = clock ? Number(clock[1]) % 12 + (clock[2] === "PM" ? 12 : 0) : NaN;
    const night = !isNaN(hour) && (hour < 6 || hour >= 20);
    const temp = fahrenheit ? now.temp_F : now.temp_C;
    if (temp === undefined) return null;
    return {temp: temp + (fahrenheit ? "°F" : "°C"), text: String(text).trim(), icon: weatherIcon(now.weatherCode, night), place: place};
}

function char(code) {
    return code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : "";
}

function plain(s) {
    return String(s || "")
        .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
        .replace(/<[^>]*>/g, "")
        .replace(/&#x([0-9a-f]+);/gi, (m, h) => char(parseInt(h, 16)))
        .replace(/&#(\d+);/g, (m, d) => char(Number(d)))
        .replace(/&quot;/g, "\"").replace(/&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
        .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&")
        .replace(/\s+/g, " ").trim();
}

// {source, items: [{title, link}]} from RSS 2.0, RSS 1.0 or Atom, or null.
// Regular expressions instead of an XML parser: feeds in the wild are
// often not well-formed, and we only need titles and links.
function parseFeed(text, max) {
    text = String(text || "");
    const blocks = text.match(/<(item|entry)[\s>][\s\S]*?<\/(item|entry)>/g) || [];
    const items = [];
    blocks.forEach(b => {
        if (items.length >= (max || 8)) return;
        const t = /<title[^>]*>([\s\S]*?)<\/title>/.exec(b);
        let link = /<link[^>]*href=["']([^"']+)["']/.exec(b);
        link = link ? link[1] : (/<link[^>]*>([\s\S]*?)<\/link>/.exec(b) || [])[1];
        const title = plain(t ? t[1] : "");
        link = plain(link);
        if (title) items.push({title: title, link: /^https?:\/\//.test(link) ? link : ""});
    });
    if (!items.length) return null;
    const head = text.split(/<(item|entry)[\s>]/)[0];
    const source = /<title[^>]*>([\s\S]*?)<\/title>/.exec(head);
    return {source: plain(source ? source[1] : ""), items: items};
}
