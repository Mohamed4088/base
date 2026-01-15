import requests
import re
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT = "sources.txt"
OUTPUT = "merged_from_sources.m3u"

HEADERS = {
    "User-Agent": "VLC/3.0.20",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

# ================== ADULT FILTER (STRONG) ==================

ADULT_WORDS = [
    "18+", "xxx", "adult", "porn", "sex", "erotic", "playboy", "xvideo",
    "redtube", "brazzers", "bangbros", "hustler", "onlyfans", "cam",
    "escort", "fetish", "milf", "anal", "hardcore", "softcore", "strip"
]

ADULT_GROUP_WORDS = [
    "xxx", "adult", "porn", "sex", "erotic"
]

# ================== COUNTRY FILTER ==================

BLOCK_COUNTRIES_WORDS = [
    "usa","canada","uk","england","britain","germany","deutsch","france","spain",
    "italy","netherlands","holland","australia","europe","asia","india","pakistan",
    "turkey","poland","romania","sweden","norway","finland","denmark","portugal",
    "brazil","mexico","argentina","latin","africa","russia","ukraine","china",
    "japan","korea","thai","vietnam","philippines","indonesia"
]

BLOCK_COUNTRY_CODES = [
    " de ", " tr ", " uk ", " fr ", " us ", " ca ", " nl ", " au ", " it ",
    " es ", " pt ", " pl ", " ro ", " se ", " no ", " fi ", " dk ", " ru ",
    " cn ", " jp ", " kr ", " in ", " pk ", " th ", " vn ", " id ", " ph ","en"
]

# ================== HELPERS ==================

def is_adult(info):
    t = " " + info.lower() + " "
    if any(w in t for w in ADULT_WORDS):
        return True
    if re.search(r'group-title="([^"]+)"', info):
        g = re.search(r'group-title="([^"]+)"', info).group(1).lower()
        if any(w in g for w in ADULT_GROUP_WORDS):
            return True
    return False


def is_blocked_country(info):
    t = " " + info.lower() + " "
    if any(w in t for w in BLOCK_COUNTRIES_WORDS):
        return True
    if any(code in t for code in BLOCK_COUNTRY_CODES):
        return True
    return False


# ================== SESSION ==================

session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[403, 404, 429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

# ================== PROCESS ==================

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

                # adult filter
                if is_adult(info):
                    i += 2
                    continue

                # country filter
                if is_blocked_country(info):
                    i += 2
                    continue

                # duplicates
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

    except Exception:
        print("  error -> skipped")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\nDONE")
print("Total kept channels:", (len(out) - 1) // 2)
print("Output:", OUTPUT)
