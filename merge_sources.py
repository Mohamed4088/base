import requests
import re

INPUT = "sources.txt"
OUTPUT = "merged_from_sources.m3u"

HEADERS = {"User-Agent": "VLC/3.0.20"}

# كلمات ممنوعة (+18)
BLOCK_WORDS = [
    "18+", "+18", "xxx", "adult", "porn", "sex", "erotic", "playboy"
]

out = ["#EXTM3U"]
seen_urls = set()
kept = 0
skipped_dup = 0
skipped_adult = 0

def is_adult(text):
    t = text.lower()
    return any(w in t for w in BLOCK_WORDS)

with open(INPUT, encoding="utf-8") as f:
    links = [l.strip() for l in f if l.strip()]

for url in links:
    print("Loading:", url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code != 200 or "#EXTM3U" not in r.text:
            print("  skip (not valid m3u)")
            continue

        lines = r.text.splitlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
                info = lines[i]
                stream = lines[i+1].strip()

                # remove adult
                if is_adult(info):
                    skipped_adult += 1
                    i += 2
                    continue

                # remove duplicates
                if stream in seen_urls:
                    skipped_dup += 1
                    i += 2
                    continue

                seen_urls.add(stream)
                out.append(info)
                out.append(stream)
                kept += 1
                i += 2
            else:
                i += 1

        print("  added")

    except Exception:
        print("  error -> skipped")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\nDONE")
print("Kept channels:", kept)
print("Removed duplicates:", skipped_dup)
print("Removed +18:", skipped_adult)
print("Output:", OUTPUT)
