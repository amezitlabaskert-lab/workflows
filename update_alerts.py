import zipfile
import requests
import xml.etree.ElementTree as ET
import json
import io
from datetime import datetime

def update_alerts():
    try:
        # A gyűjtőlink, ami mindig a legfrissebb csomagra mutat
        url = "https://odp.met.hu/weather/warnings/wadata/wadata.xml.zip"
        
        # Böngészőnek álcázzuk magunkat (User-Agent), hogy ne kapjunk 403/404-es hibát
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Lekérés indítása: {url}")
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status() # Hibát dob, ha nem sikerül a letöltés
        
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            # Kivesszük a ZIP-ben található legelső (és egyetlen) XML fájlt
            xml_filename = z.namelist()[0]
            with z.open(xml_filename) as f:
                tree = ET.parse(f)
                root = tree.getroot()

        results = []
        # Megkeressük az összes riasztást (alert) az XML-ben
        for alert in root.findall('.//alert'):
            phenom = alert.find('phenomena').text
            level = alert.find('level').text
            # Összeszedjük a járásokat, amikre ez a riasztás érvényes
            districts = [d.text for d in alert.findall('.//district')]
            
            results.append({
                "v": phenom,
                "sz": level,
                "j": districts
            })

        # Az aktuális idő lekérése magyar formátumban
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        output_data = {
            "alerts": results,
            "source": "HungaroMet Nonprofit Zrt.",
            "updated": now,
            "file": xml_filename # Logoljuk, melyik XML-t dolgoztuk fel
        }

        with open('riasztasok.json', 'w', encoding='utf-8') as out:
            json.dump(output_data, out, ensure_ascii=False, indent=2)
            
        print(f"Sikeres frissítés! Feldolgozott fájl: {xml_filename}")

    except Exception as e:
        print(f"Hiba történt: {e}")
        # Hiba esetén is mentsünk egy állapotot, hogy lássuk, baj van
        error_data = {"error": str(e), "updated": datetime.now().strftime('%Y-%m-%d %H:%M')}
        with open('riasztasok.json', 'w', encoding='utf-8') as out:
            json.dump(error_data, out, ensure_ascii=False)

if __name__ == "__main__":
    update_alerts()
