import zipfile
import requests
import xml.etree.ElementTree as ET
import json
import io
import re
from datetime import datetime

def update_alerts():
    try:
        # A mappa URL-je, amit a képeden láttunk
        base_url = "https://odp.met.hu/weather/warnings/wadata/wahx/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Mappa listázása: {base_url}")
        # 1. Beolvassuk a mappa tartalmát
        index_page = requests.get(base_url, headers=headers, timeout=15)
        index_page.raise_for_status()

        # 2. Megkeressük az összes .xml.zip fájlt a listában
        zips = re.findall(r'href="([^"]+\.xml\.zip)"', index_page.text)
        
        if not zips:
            raise Exception("Nem találtam ZIP fájlt a mappában! Lehet, hogy üres?")

        # 3. Kiválasztjuk a név alapján legutolsót (ez a legfrissebb időpontú)
        latest_zip = sorted(zips)[-1]
        url = base_url + latest_zip
        
        print(f"Legfrissebb fájl letöltése: {url}")
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        # 4. Kicsomagoljuk a ZIP-et a memóriában
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            xml_filename = z.namelist()[0]
            with z.open(xml_filename) as f:
                tree = ET.parse(f)
                root = tree.getroot()

        results = []
        # 5. Feldolgozzuk a riasztásokat
        for alert in root.findall('.//alert'):
            phenom = alert.find('phenomena').text
            level = alert.find('level').text
            # Összeszedjük a járásokat
            districts = [d.text for d in alert.findall('.//district')]
            
            results.append({
                "v": phenom,
                "sz": level,
                "j": districts
            })

        # Időbélyeg a mentéshez
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        output_data = {
            "alerts": results,
            "source": "HungaroMet Nonprofit Zrt.",
            "updated": now,
            "file": latest_zip
        }

        # 6. Mentés a riasztasok.json fájlba
        with open('riasztasok.json', 'w', encoding='utf-8') as out:
            json.dump(output_data, out, ensure_ascii=False, indent=2)
            
        print(f"Sikeres frissítés! Forrásfájl: {latest_zip}")

    except Exception as e:
        print(f"Hiba történt: {e}")
        error_data = {
            "error": str(e), 
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        with open('riasztasok.json', 'w', encoding='utf-8') as out:
            json.dump(error_data, out, ensure_ascii=False)

if __name__ == "__main__":
    update_alerts()
