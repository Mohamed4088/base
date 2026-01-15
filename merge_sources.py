import requests

INPUT = "sources.txt"
OUTPUT = "merged_from_sources.m3u"

headers = {"User-Agent": "VLC/3.0.20"}

out = ["#EXTM3U"]

with open(INPUT, encoding="utf-8") as f:
    links = [l.strip() for l in f if l.strip()]

for url in links:
    print("Loading:", url)
    try:
        r = requests.get(url, headers=headers, timeout=60)
        if r.status_code != 200 or "#EXTM3U" not in r.text:
            print("  skip (not valid m3u)")
            continue

        lines = r.text.splitlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
                out.append(lines[i])
                out.append(lines[i+1])
                i += 2
            else:
                i += 1

        print("  added")

    except Exception as e:
        print("  error -> skipped")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("DONE ->", OUTPUT)
