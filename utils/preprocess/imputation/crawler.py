import html
import re
import time
import requests
from bs4 import BeautifulSoup

def strip_html(raw_html: str) -> str:
    """Matches the exact text-cleaning format used in SteamGames_test_100.csv."""
    if not raw_html or not isinstance(raw_html, str):
        return ""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_requirements_html(req_obj) -> dict:
    """Extracts OS, CPU, Memory, and GPU from pc/mac/linux_requirements JSON block."""
    res = {"OsRequirement": None, "CpuRequirement": None, "MemoryRequirement": None, "GpuRequirement": None}
    
    # Steam API sometimes returns [] instead of {} when requirements are empty
    if not isinstance(req_obj, dict):
        return res
        
    min_html = req_obj.get("minimum", "")
    if not min_html:
        return res

    soup = BeautifulSoup(min_html, "html.parser")
    # Extract <li> items; fallback to splitting by <br> for older games
    items = [li.get_text(" ", strip=True) for li in soup.find_all("li")]
    if not items:
        items = [strip_html(chunk) for chunk in min_html.split("<br>")]

    for text in items:
        if re.match(r'^OS\s*\*?\s*:', text, re.IGNORECASE):
            res["OsRequirement"] = text.split(":", 1)[1].strip()
        elif re.match(r'^(Processor|CPU)\s*:', text, re.IGNORECASE):
            res["CpuRequirement"] = text.split(":", 1)[1].strip()
        elif re.match(r'^Memory\s*:', text, re.IGNORECASE):
            res["MemoryRequirement"] = text.split(":", 1)[1].strip()
        elif re.match(r'^(Graphics|Video Card|GPU)\s*:', text, re.IGNORECASE):
            res["GpuRequirement"] = text.split(":", 1)[1].strip()
            
    return res

def fetch_steam_app_data(appid: int, session: requests.Session) -> dict | None:
    """Fetches appdetails JSON from Steam API with 429 backoff."""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english"
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code == 200:
                payload = resp.json().get(str(appid), {})
                if payload.get("success") and "data" in payload:
                    data = payload["data"]
                    
                    # Check PC requirements first, fallback to Linux or Mac if PC is empty
                    reqs = parse_requirements_html(data.get("pc_requirements"))
                    if not any(reqs.values()):
                        reqs = parse_requirements_html(data.get("linux_requirements"))
                    if not any(reqs.values()):
                        reqs = parse_requirements_html(data.get("mac_requirements"))
                        
                    # Extract description & genres
                    desc = strip_html(data.get("short_description", ""))
                    genres_list = [g["description"] for g in data.get("genres", []) if "description" in g]
                    
                    return {
                        "Description": desc or None,
                        "Genres": ",".join(genres_list) if genres_list else None,
                        **reqs
                    }
                return None  # Game delisted or success == False
            elif resp.status_code == 429:
                print(f"[Rate Limit 429] Sleeping 60s on Appid {appid}...")
                time.sleep(60)
        except Exception as e:
            print(f"[Error] Appid {appid}: {e}")
            time.sleep(2)
    return None