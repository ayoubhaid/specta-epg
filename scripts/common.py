import re, unicodedata

QUALITY = r"\b(hd|fhd|uhd|sd|4k|8k|hevc|raw|vip|50fps|60fps|backup|multi ?audio|lq|ultra|ziggo|25fps|bk|plus ?hd)\b"
VOD_RE = re.compile(r"\(\d{4}\)|^(EN|FR|ES|DE|IT|PT) - ", re.I)

COUNTRY = {  # region_code in CSV -> iptv-org country suffix
    "UK": "uk", "IT": "it", "GR": "gr", "CA": "ca", "NL": "nl", "DE": "de", "FR": "fr",
    "PL": "pl", "US": "us", "ES": "es", "SP": "es", "NZ": "nz", "AU": "au", "CZ": "cz",
    "MXC": "mx", "LAT": "mx", "RS": "rs", "BE": "be", "TR": "tr", "PT": "pt", "BR": "br",
    "SWE": "se", "HR": "hr", "BA": "ba", "ARG": "ar", "AT": "at", "ALB": "al", "MT": "mt",
    "SR": "rs", "SA": "sa", "UGA": "ug",
}

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"^[A-Za-z0-9+\- ]{1,12}\|\s*", "", s)      # strip "UK| " style prefixes
    s = s.lower().replace("+", " plus ").replace("&", " and ")
    s = re.sub(QUALITY, " ", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def is_vod(name: str) -> bool:
    return bool(VOD_RE.search(name))

def split_ids(v):
    if v is None or str(v) == "nan":
        return []
    return [x.strip() for x in str(v).split("|") if x.strip()]
