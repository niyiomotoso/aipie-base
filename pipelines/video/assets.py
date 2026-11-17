"""Find, fetch and rights-check B-roll images. Builds the rights ledger.

Source priority: Niyi's own photos > Wikimedia Commons > Pixabay > AI illustration.
Every asset carries a licence record; render.py refuses anything without one.
"""
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config as C

BLOCKED_LICENCES = ("NonCommercial", "NoDerivatives", "CC BY-NC", "CC BY-ND")


def _get(url: str, tries: int = 4) -> bytes:
    """Wikimedia throttles hard without a descriptive User-Agent. Back off on 429."""
    for n in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": C.USER_AGENT}),
                timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == tries - 1:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 5 * (n + 1)
            print(f"    429 from Wikimedia, waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def _strip(html) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def search_wikimedia(query: str, limit: int = 6) -> list:
    params = {"action": "query", "generator": "search", "gsrsearch": query,
              "gsrnamespace": "6", "gsrlimit": str(limit), "prop": "imageinfo",
              "iiprop": "url|size|extmetadata", "format": "json", "formatversion": "2"}
    data = json.loads(_get(C.WIKIMEDIA_API + "?" + urllib.parse.urlencode(params)))
    out = []
    for p in data.get("query", {}).get("pages", []):
        ii = (p.get("imageinfo") or [{}])[0]
        em = ii.get("extmetadata", {})
        lic = em.get("LicenseShortName", {}).get("value", "?")
        out.append({
            "title": p["title"][5:], "url": ii.get("url"),
            "width": ii.get("width"), "height": ii.get("height"),
            "license_code": lic,
            "license_url": em.get("LicenseUrl", {}).get("value"),
            "creator_name": _strip(em.get("Artist", {}).get("value")),
            "attribution_required": em.get("AttributionRequired", {}).get("value") == "true",
            "restrictions": em.get("Restrictions", {}).get("value", ""),
            "source_landing_url": ii.get("descriptionurl"),
            "blocked": any(b.lower() in lic.lower() for b in BLOCKED_LICENCES),
        })
    return out


def search_pixabay(query: str, env: dict, vertical: bool = True) -> list:
    """Default key caps at largeImageURL (~1280px), so stock is inset-only."""
    key = env.get("PIXABAY_API_KEY")
    if not key:
        print("  PIXABAY_API_KEY not set - skipping stock")
        return []
    params = {"key": key, "q": query, "image_type": "photo", "safesearch": "true",
              "per_page": "8"}
    if vertical:
        params["orientation"] = "vertical"
    try:
        data = json.loads(_get(C.PIXABAY_API + "?" + urllib.parse.urlencode(params)))
    except Exception as e:
        print(f"  pixabay failed, continuing without stock: {e}")
        return []
    return [{"title": h["tags"][:70], "url": h["largeImageURL"],
             "width": h.get("imageWidth"), "height": h.get("imageHeight"),
             "license_code": "Pixabay Content License", "license_url": None,
             "creator_name": h.get("user"), "attribution_required": False,
             "restrictions": "", "source_landing_url": h.get("pageURL"),
             "blocked": False, "capped_px": 1280}
            for h in data.get("hits", [])]


def fetch(cand: dict, slug: str, moment: str, dest: pathlib.Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    ext = pathlib.Path(urllib.parse.urlparse(cand["url"]).path).suffix or ".jpg"
    local = dest / f"{slug}{ext}"
    if not local.exists():
        local.write_bytes(_get(cand["url"]))
        time.sleep(2)           # be a good citizen between downloads
    data = local.read_bytes()
    rec = dict(cand)
    rec.pop("blocked", None)
    rec.update({
        "slug": slug, "moment": moment, "local_path": str(local),
        "sha256": hashlib.sha256(data).hexdigest(),
        "direct_file_url": cand["url"],
        "attribution_string": f'"{cand["title"]}" by '
                              f'{cand.get("creator_name") or "unknown"}, '
                              f'{cand["license_code"]}',
        "review_required": bool(cand.get("restrictions")),
    })
    return rec


def own_photo(path: pathlib.Path, slug: str, moment: str) -> dict:
    data = path.read_bytes()
    return {"slug": slug, "moment": moment, "source": "creator",
            "title": path.name, "local_path": str(path),
            "sha256": hashlib.sha256(data).hexdigest(),
            "license_code": "owned", "attribution_required": False,
            "creator_name": "Niyi Omotoso", "restrictions": "",
            "review_required": False, "attribution_string": "own photograph"}


def write_ledger(project: str, records: list) -> pathlib.Path:
    work = C.project_dir(project)
    (work / "assets.json").write_text(json.dumps(records, indent=2))
    need = [r for r in records if r.get("attribution_required")]
    if need:
        (work / "credits.txt").write_text(
            "Image credits\n" + "\n".join(
                f"- {r['attribution_string']} - {r.get('source_landing_url','')}"
                for r in need) + "\n")
    print(f"assets.json: {len(records)} assets, {len(need)} need attribution")
    for r in records:
        flag = "  REVIEW" if r.get("review_required") else ""
        print(f"  {r['slug']:<14} {r['license_code']:<24} "
              f"{r.get('width','?')}x{r.get('height','?')}{flag}")
    return work / "assets.json"


def main(project: str, *queries: str) -> int:
    """Search helper. The model picks from the results and calls fetch()."""
    env = C.load_env()
    for q in queries:
        print(f"\n=== wikimedia: {q}")
        for c in search_wikimedia(q):
            mark = "BLOCKED" if c["blocked"] else ("REVIEW" if c["restrictions"] else "ok")
            print(f"  [{mark:<7}] {c['title'][:58]}")
            print(f"            {c['width']}x{c['height']}  {c['license_code']}  "
                  f"attr={'yes' if c['attribution_required'] else 'no'}"
                  + (f"  restrictions={c['restrictions']}" if c["restrictions"] else ""))
        print(f"\n=== pixabay: {q}")
        for c in search_pixabay(q, env)[:4]:
            print(f"  [inset  ] {c['title'][:58]}  ({c['width']}x{c['height']}, "
                  f"served at <=1280px)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: python3 -m pipelines.video.assets <project> <query> [query...]")
    sys.exit(main(sys.argv[1], *sys.argv[2:]))
