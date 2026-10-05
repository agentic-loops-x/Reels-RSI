"""Find and download freely licensed historical images from Wikimedia Commons.

History films live on real artifacts: period paintings, portraits, maps, manuscripts, photos.
Code draws diagrams well and people badly — a public-domain portrait with a slow Ken Burns move
and code layers on top (labels, lines, highlights) beats a clip-art figure.

  search:   evofilm commons search "Napoleon Austerlitz painting" [--limit 12]
  download: evofilm commons get --project <dir> --name napoleon "File:Gérard - La bataille d'Austerlitz.jpg" [--width 2400]

Only these licenses are accepted: Public domain, PD-*, CC0, CC BY, CC BY-SA (any version).
Every download is appended to <project>/CREDITS.md with author, license and source URL —
CC BY/BY-SA REQUIRE that attribution in the video description (and BY-SA share-alike).
Files land in <project>/public/<name>.<ext>.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "evofilm/0.1 (local video tool)"}
OK = re.compile(r"^(public domain|pd\b|pd-|cc0|cc by(-sa)?\b|cc-by(-sa)?\b)", re.I)


def api(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.loads(r.read())


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def info(titles, width=None):
    params = {"action": "query", "titles": "|".join(titles), "prop": "imageinfo",
              "iiprop": "url|extmetadata|size|mime"}
    if width:
        params["iiurlwidth"] = width
    pages = api(params)["query"]["pages"].values()
    out = []
    for p in pages:
        if "imageinfo" not in p:
            continue
        ii = p["imageinfo"][0]
        md = ii.get("extmetadata", {})
        lic = strip_html(md.get("LicenseShortName", {}).get("value", ""))
        out.append({
            "title": p["title"], "license": lic, "ok": bool(OK.match(lic)),
            "author": strip_html(md.get("Artist", {}).get("value", "")) or "unknown",
            "date": strip_html(md.get("DateTimeOriginal", {}).get("value", "")),
            "desc": strip_html(md.get("ImageDescription", {}).get("value", ""))[:140],
            "size": f'{ii.get("width")}×{ii.get("height")}', "mime": ii.get("mime"),
            "url": ii.get("thumburl") or ii["url"], "page": ii.get("descriptionurl"),
        })
    return out


def cmd_search(q, limit):
    res = api({"action": "query", "list": "search", "srsearch": f"{q} filetype:bitmap", "srnamespace": 6,
               "srlimit": limit})
    titles = [r["title"] for r in res["query"]["search"]]
    if not titles:
        print("no results")
        return
    for it in info(titles):
        flag = "✓" if it["ok"] else "✗"
        print(f'{flag} {it["title"]}\n    {it["license"]} · {it["author"][:60]} · {it["date"][:30]} · {it["size"]}\n    {it["desc"]}')


def cmd_get(project, name, title, width):
    items = info([title], width)
    if not items:
        sys.exit(f"✗ not found: {title}")
    it = items[0]
    if not it["ok"]:
        sys.exit(f"✗ license not allowed: {it['license']} — pick a public-domain / CC0 / CC BY(-SA) file")
    ext = ".png" if "png" in (it["mime"] or "") else ".jpg"
    dst = Path(project) / "public" / f"{name}{ext}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(it["url"], headers=UA), timeout=120) as r:
        dst.write_bytes(r.read())
    credits = Path(project) / "CREDITS.md"
    if not credits.exists():
        credits.write_text("# Credits — third-party images (put CC BY / BY-SA lines in the video description)\n\n", "utf-8")
    with credits.open("a", encoding="utf-8") as fh:
        fh.write(f'- public/{dst.name} — "{it["title"][5:]}" by {it["author"]} · {it["license"]} · {it["page"]}\n')
    print(f"✓ public/{dst.name} ({it['license']}) — credited in CREDITS.md")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="evofilm commons")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=12)
    g = sub.add_parser("get"); g.add_argument("title"); g.add_argument("--project", default=".")
    g.add_argument("--name", required=True); g.add_argument("--width", type=int, default=2400)
    a = ap.parse_args(argv)
    cmd_search(a.query, a.limit) if a.cmd == "search" else cmd_get(a.project, a.name, a.title, a.width)


if __name__ == "__main__":
    main()
