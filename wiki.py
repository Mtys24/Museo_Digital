import json
import hashlib
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request

CACHE_DIR = Path("wiki_cache")
CACHE_DIR.mkdir(exist_ok=True)

USER_AGENT = "MuseoDigital/1.0 (chatbot educativo)"
SEARCH_URL = "https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=3&srprop=snippet"
SUMMARY_URL = "https://es.wikipedia.org/api/rest_v1/page/summary/{title}"

session = {}


def _cache_key(query):
    return hashlib.md5(query.encode("utf-8")).hexdigest()


def _load_cache(key):
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(key, data):
    path = CACHE_DIR / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _fetch_json(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search(query, max_length=800):
    key = _cache_key(query)
    cached = _load_cache(key)
    if cached:
        return cached

    search_url = SEARCH_URL.format(query=quote(query))
    try:
        data = _fetch_json(search_url)
    except Exception:
        return None

    results = data.get("query", {}).get("search", [])
    if not results:
        _save_cache(key, None)
        return None

    best = results[0]
    title = best["title"]

    summary_url = SUMMARY_URL.format(title=quote(title))
    try:
        summary_data = _fetch_json(summary_url)
    except Exception:
        snippet = best.get("snippet", "")
        snippet = snippet.replace("<span class=\"searchmatch\">", "").replace("</span>", "")
        if snippet:
            _save_cache(key, {"title": title, "summary": snippet[:max_length]})
            return {"title": title, "summary": snippet[:max_length]}
        _save_cache(key, None)
        return None

    extract = summary_data.get("extract", "")
    if not extract:
        _save_cache(key, None)
        return None

    result = {
        "title": title,
        "summary": extract[:max_length],
        "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
    }
    _save_cache(key, result)
    return result
