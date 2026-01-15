import requests
import re
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT = "sources.txt"
OUTPUT = "merged_from_sources.m3u"

# Headers تقلد IPTV Player
HEADERS = {
    "User-Agent": "VLC/3.0.20",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

# كلمات ممنوعة
BLOCK_WORDS = ["18+", "+18", "xxx", "adult", "porn", "sex", "erotic", "playboy"]

def is_adult(text):
    t = text.lower()
    return any(w in t for w in BLOCK_WORDS)

# Session + Retry
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[403, 404, 429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

out = ["#EXTM3U"]
seen_urls = set()

with open(INPUT, encoding="utf-8") as f:
    links = [l.strip() for l in f if l.strip()]

for url in links:
    print("Loading:", url)
    try:
        r = session.get(url, headers=HEADERS, timeout=60, verify=False)

        if r.status_code != 200 or "#EXTM3U" not in r.text:
            print("  skip (not valid m3u)")
            continue

        lines = r.text.splitlines()
        i = 0
        added = 0

        while i < len(lines):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
                info = lines[i]
                stream = lines[i + 1].strip()

                if is_adult(info):
                    i += 2
                    continue

                if stream in seen_urls:
                    i += 2
                    continue

                seen_urls.add(stream)
                out.append(info)
                out.append(stream)
                added += 1
                i += 2
            else:
                i += 1

        print(f"  added {added} channels")

    except Exception as e:
        print("  error -> skipped")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\nDONE")
print("Total kept channels:", len(out)//2)
print("Output:", OUTPUT)
