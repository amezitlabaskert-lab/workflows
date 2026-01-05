import zipfile
import requests
import xml.etree.ElementTree as ET
import json
import io
import re
from datetime import datetime

def get_latest_from_folder(base_url, headers):
    index_page = requests.get(base_url, headers=headers, timeout=15)
    index_page.raise_for_status()
    zips = re.findall(r'href="([^"]+\.xml\.zip)"', index_page.text)
    if not zips: return None
    latest_zip = sorted(zips)[-1]
    return base_url + latest_zip, latest_zip

def update_alerts():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    results = []
    processed_files = []

    try:
        # MAPPA 1: Aktuális riasztások (MOST)
        folders = [
            "https://odp.met.hu/weather/warnings/wahx/", # Riasztás
            "https://odp.met.hu/weather/warnings/wbhx/"  # Figyelmeztetés (Holnap)
        ]

        for folder in folders:
            info = get_latest_from_folder(folder, headers)
            if not info: continue
            url, fname = info
            processed_files.append(fname)
            
            r = requests.get(url, headers=headers, timeout=15)
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                xml_filename = z.namelist()[0]
                with z.open(xml_filename) as f:
                    root = ET.parse(f).getroot()
                    for alert in root.findall('.//alert'):
                        phenom = alert.find('phenomena').text
                        level = alert.find('level').text
                        districts = [d.text for d in alert.findall('.//district')]
                        results.append({"v": phenom, "sz": level, "j": districts, "f": fname[:4]}) # f=wahx vagy wbhx

        output_data = {
            "alerts": results,
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "files": processed_files
        }

        with open('riasztasok.json', 'w', encoding='utf-8') as out:
            json.dump(output_data, out, ensure_ascii=False, indent=2)
        print(f"Siker! Beolvasva: {processed_files}")

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    update_alerts()
