import os
import requests
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
PEXELS_URL = "https://api.pexels.com/videos/search"
PIXABAY_URL = "https://pixabay.com/api/videos/"

_RETRY = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
)

@retry(**_RETRY)
def _search_pexels(query: str, per_page: int = 3) -> list[dict]:
    if not PEXELS_API_KEY: return []
    resp = requests.get(
        PEXELS_URL,
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "per_page": per_page, "orientation": "landscape"},
        timeout=8,
    )
    resp.raise_for_status()
    out = []
    for v in resp.json().get("videos", []):
        if not v.get("video_files"): continue
        hd = next((f for f in v["video_files"] if f.get("quality") == "hd"), v["video_files"][0])
        out.append({
            "source": "pexels",
            "video_url": hd["link"],
            "thumbnail_url": v["image"],
            "duration_seconds": float(v["duration"]),
            "resolution": f"{hd.get('width', 0)}x{hd.get('height', 0)}",
        })
    return out

@retry(**_RETRY)
def _search_pixabay(query: str, per_page: int = 3) -> list[dict]:
    if not PIXABAY_API_KEY: return []
    resp = requests.get(
        PIXABAY_URL,
        params={"key": PIXABAY_API_KEY, "q": query, "per_page": per_page},
        timeout=8,
    )
    resp.raise_for_status()
    out = []
    for hit in resp.json().get("hits", []):
        videos = hit.get("videos", {})
        if "medium" not in videos: continue
        m = videos["medium"]
        out.append({
            "source": "pixabay",
            "video_url": m["url"],
            "thumbnail_url": m["thumbnail"],
            "duration_seconds": float(hit.get("duration", 0.0)),
            "resolution": f"{m.get('width', 0)}x{m.get('height', 0)}",
        })
    return out

@lru_cache(maxsize=256)
def search_broll(query: str) -> tuple[dict, ...]:
    try:
        results = _search_pexels(query)
        if results: return tuple(results)
    except requests.exceptions.RequestException:
        pass
    try:
        return tuple(_search_pixabay(query))
    except requests.exceptions.RequestException:
        return ()

MAX_CONCURRENT_BROLL_REQUESTS = 4

def search_broll_batch(queries: list[str]) -> dict[str, tuple[dict, ...]]:
    unique_queries = list(dict.fromkeys(queries))
    results: dict[str, tuple[dict, ...]] = {}
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_BROLL_REQUESTS) as pool:
        future_to_query = {pool.submit(search_broll, q): q for q in unique_queries}
        for future in as_completed(future_to_query):
            q = future_to_query[future]
            try:
                results[q] = future.result()
            except Exception:
                results[q] = ()
    return results