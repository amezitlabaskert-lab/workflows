import zipfile, requests, xml.etree.ElementTree as ET, json, io

def update_alerts():
    try:
        url = "https://odp.met.hu/weather/warnings/wadata/wadata.xml.zip"
        r = requests.get(url, timeout=10)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            with z.open(z.namelist()[0]) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                results = []
                for alert in root.findall('.//alert'):
                    phenom = alert.find('phenomena').text
                    level = alert.find('level').text
                    districts = [d.text for d in alert.findall('.//district')]
                    results.append({"v": phenom, "sz": level, "j": districts})
                
                with open('riasztasok.json', 'w', encoding='utf-8') as out:
                    json.dump({"alerts": results, "source": "HungaroMet Nonprofit Zrt.", "updated": "2026-01-05"}, out, ensure_ascii=False)
        print("Sikeres frissítés!")
    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    update_alerts()
