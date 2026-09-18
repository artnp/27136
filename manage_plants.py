#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Garden Plan Management Script (ระบบจัดการข้อมูลและแปลนต้นไม้หลังบ้าน)
- ป้อนนำเข้า / แก้ไข / ลบข้อมูลต้นไม้
- กำหนดโซน 1 ถึง โซน 4 ในแปลนบ้าน plan.png
- ดึงข้อมูลสรรพคุณ โภชนาการ ข้อห้าม และภาพใบไม้ฟรี (ไม่ต้องใช้ API key)
- อัปเดตไฟล์ข้อมูล data/plants.json และ index.html พร้อมอัปโหลดขึ้น GitHub
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANTS_FILE = os.path.join(BASE_DIR, "data", "plants.json")
HERBS_DB_FILE = os.path.join(BASE_DIR, "data", "herbs_db.json")
IMAGES_DIR = os.path.join(BASE_DIR, "images", "plants")
INDEX_HTML_FILE = os.path.join(BASE_DIR, "index.html")

# Default coordinates for each zone (percentage from top-left)
ZONE_DEFAULTS = {
    "zone_1": {"name": "โซน 1", "default_x": 15.0, "default_y": 72.0, "color": "#10b981", "desc": "สวนครัวและไม้กระถางริมรั้ว (ล่างซ้าย)"},
    "zone_2": {"name": "โซน 2", "default_x": 70.0, "default_y": 72.0, "color": "#3b82f6", "desc": "แปลงพืชสมุนไพรและแปลงผักยกพื้น (ล่างขวา)"},
    "zone_3": {"name": "โซน 3", "default_x": 25.0, "default_y": 15.0, "color": "#8b5cf6", "desc": "ซุ้มไม้เลื้อยและพืชผักแนวดิ่ง (บนซ้าย)"},
    "zone_4": {"name": "โซน 4", "default_x": 73.0, "default_y": 16.0, "color": "#f59e0b", "desc": "โรงเรือนสมุนไพรและพืชยาเฉพาะทาง (บนขวา)"}
}

def load_json(filepath, default_val=None):
    if not os.path.exists(filepath):
        return default_val if default_val is not None else {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] เกิดข้อผิดพลาดในการอ่านไฟล์ {filepath}: {e}")
        return default_val if default_val is not None else {}

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_wikipedia_info(plant_name):
    """
    ดึงข้อมูลและรูปภาพจาก Wikipedia ภาษาไทย ฟรี 100% ไม่ต้องใช้ API Key
    """
    try:
        url = f"https://th.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(plant_name)}"
        headers = {"User-Agent": "HomeGardenBot/1.0 (bot@garden.local)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            extract = data.get("extract", "")
            image_url = ""
            if "originalimage" in data:
                image_url = data["originalimage"].get("source", "")
            elif "thumbnail" in data:
                image_url = data["thumbnail"].get("source", "")
            
            return {
                "found": True,
                "title": data.get("title", plant_name),
                "summary": extract,
                "image_url": image_url
            }
    except Exception:
        return {"found": False}

def find_herb_in_db(name_query):
    """
    ค้นหาข้อมูลพืชในฐานข้อมูลสมุนไพรออฟไลน์ herbs_db.json
    """
    db = load_json(HERBS_DB_FILE, {"herbs": []})
    herbs = db.get("herbs", [])
    query = name_query.strip().lower()
    
    # 1. ค้นหาชื่อตรงกันเป๊ะ
    for h in herbs:
        if query in h["name"].lower() or h["name"].lower() in query:
            return h
            
    # 2. ค้นหาชื่อวิทยาศาสตร์หรือภาษาอังกฤษ
    for h in herbs:
        if query in h.get("common_name", "").lower() or query in h.get("scientific_name", "").lower():
            return h
            
    return None

def download_image(url, save_name):
    """
    ดาวน์โหลดรูปภาพมาเก็บไว้ใน images/plants/ เพื่อให้ดูแบบออฟไลน์ได้
    """
    if not url or not url.startswith("http"):
        return url
    try:
        os.makedirs(IMAGES_DIR, exist_ok=True)
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"
            
        filename = f"{save_name}{ext}"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return f"images/plants/{filename}"
    except Exception as e:
        print(f"[-] ไม่สามารถดาวน์โหลดรูปได้ ({e}) จะใช้ URL ออนไลน์แทน")
        return url

def list_plants():
    data = load_json(PLANTS_FILE, {"plants": []})
    plants = data.get("plants", [])
    if not plants:
        print("\n[i] ยังไม่มีข้อมูลต้นไม้ในระบบ")
        return []
    
    print("\n" + "="*70)
    print(" รายการต้นไม้ในแปลนบ้านปัจจุบัน")
    print("="*70)
    print(f"{'ลำดับ':<6} {'โซน':<8} {'ชื่อต้นไม้':<22} {'พิกัด X, Y':<15} {'ประเภท'}")
    print("-" * 70)
    for idx, p in enumerate(plants, 1):
        zone_str = p.get("zone_name", p.get("zone_id", "-"))
        name_str = p.get('name', 'ไม่ระบุชื่อ')
        coord_str = f"({p.get('x', 0):.1f}%, {p.get('y', 0):.1f}%)"
        cat_str = p.get("category", "-")
        print(f"{idx:<6} {zone_str:<8} {name_str:<22} {coord_str:<15} {cat_str}")
    print("="*70)
    return plants

def add_plant():
    print("\n" + "="*50)
    print(" ➕ เพิ่มข้อมูลต้นไม้ใหม่ลงในแปลนบ้าน")
    print("="*50)
    name = input("ระบุชื่อต้นไม้ (เช่น มะนาว, กะเพรา, ขมิ้นชัน): ").strip()
    if not name:
        print("[!] ไม่ได้ระบุชื่อ ยกเลิกการเพิ่ม")
        return
        
    print(f"\n[*] กำลังดึงข้อมูลและภาพใบไม้สำหรับ '{name}' (ฟรี 100% ไม่ใช้ API Key)...")
    herb_info = find_herb_in_db(name)
    wiki_info = None
    
    if herb_info:
        print(f"[✓] พบข้อมูลในฐานข้อมูลสมุนไพร: '{herb_info['name']}' ({herb_info.get('scientific_name', '')})")
    else:
        print("[-] ไม่พบในฐานข้อมูลออฟไลน์ กำลังค้นหาต่อใน Wikipedia...")
        wiki_info = fetch_wikipedia_info(name)
        if wiki_info.get("found"):
            print(f"[✓] พบข้อมูลจาก Wikipedia: {wiki_info.get('title')}")
        else:
            print("[-] ไม่พบข้อมูลอัตโนมัติ คุณสามารถกรอกรายละเอียดเพิ่มเติมเองได้")
            
    print("\nเลือกโซนที่ปลูกในแปลนบ้าน:")
    print("  1. โซน 1 (ล่างซ้าย - ไม้กระถางริมรั้ว/สวนครัว)")
    print("  2. โซน 2 (ล่างขวา - แปลงสมุนไพรและแปลงผักยกพื้น)")
    print("  3. โซน 3 (บนซ้าย - ซุ้มไม้เลื้อยและผักแนวดิ่ง)")
    print("  4. โซน 4 (บนขวา - โรงเรือนสมุนไพรเฉพาะทาง)")
    
    zone_choice = input("เลือกโซน (1-4) [ค่าเริ่มต้น 1]: ").strip()
    zone_key = f"zone_{zone_choice}" if zone_choice in ["1", "2", "3", "4"] else "zone_1"
    zone_cfg = ZONE_DEFAULTS[zone_key]
    
    custom_coord = input(f"ต้องการระบุพิกัด X, Y หรือไม่ (กด Enter เพื่อใช้พิกัดเริ่มต้นโซน {zone_cfg['default_x']}%, {zone_cfg['default_y']}%): ").strip()
    if custom_coord and "," in custom_coord:
        try:
            parts = custom_coord.split(",")
            pos_x = float(parts[0].strip())
            pos_y = float(parts[1].strip())
        except ValueError:
            pos_x, pos_y = zone_cfg["default_x"], zone_cfg["default_y"]
    else:
        pos_x, pos_y = zone_cfg["default_x"], zone_cfg["default_y"]

    # รวบรวมข้อมูล
    scientific_name = herb_info.get("scientific_name", "") if herb_info else ""
    category = herb_info.get("category", "สมุนไพร / ผักสวนครัว") if herb_info else "พืชทั่วไป"
    icon = herb_info.get("icon", "🌱") if herb_info else "🌿"
    leaf_image = herb_info.get("leaf_image", "") if herb_info else (wiki_info.get("image_url", "") if wiki_info else "")
    leaf_desc = herb_info.get("leaf_description", "") if herb_info else ""
    med_props = herb_info.get("medicinal_properties", []) if herb_info else []
    
    if not med_props and wiki_info and wiki_info.get("summary"):
        med_props = [wiki_info.get("summary")[:200] + "..."]
        
    edible_info = herb_info.get("edible_parts_and_nutrition", {
        "edible_parts": "ใบ, ผล หรือยอดอ่อน",
        "nutrients": "วิตามินและสารต้านอนุมูลอิสระจากพืชธรรมชาติ",
        "energy_and_body_effects": "เสริมสร้างสุขภาพและให้พลังงานตามธรรมชาติ"
    }) if herb_info else {
        "edible_parts": "ใบ หรือ ยอดอ่อน",
        "nutrients": "วิตามินและแร่ธาตุธรรมชาติ",
        "energy_and_body_effects": "ช่วยบำรุงสุขภาพ"
    }
    
    contraindications = herb_info.get("contraindications", "ควรรับประทานในปริมาณที่พอเหมาะ ผู้มีโรคประจำตัวควรปรึกษาแพทย์") if herb_info else "ควรรับประทานในปริมาณที่เหมาะสม"
    
    note = input("บันทึกเพิ่มเติม (เช่น วันที่ปลูก หรือวิธีดูแล) [Enter เพื่อข้าม]: ").strip()
    
    # ดาวน์โหลดรูปเก็บไว้ในเครื่อง
    safe_name = f"plant_{int(time.time())}"
    if leaf_image:
        local_img = download_image(leaf_image, safe_name)
        if local_img:
            leaf_image = local_img

    plant_obj = {
        "id": safe_name,
        "name": name,
        "scientific_name": scientific_name,
        "zone_id": zone_key,
        "zone_name": zone_cfg["name"],
        "x": round(pos_x, 1),
        "y": round(pos_y, 1),
        "category": category,
        "icon": icon,
        "leaf_image": leaf_image,
        "leaf_description": leaf_desc,
        "planted_date": datetime.now().strftime("%Y-%m-%d"),
        "note": note if note else f"ปลูกใน{zone_cfg['name']}",
        "medicinal_properties": med_props,
        "edible_parts_and_nutrition": edible_info,
        "contraindications": contraindications
    }
    
    data = load_json(PLANTS_FILE, {"plants": []})
    if "plants" not in data:
        data["plants"] = []
    data["plants"].append(plant_obj)
    data["updated_at"] = datetime.now().isoformat()
    save_json(PLANTS_FILE, data)
    
    print(f"\n[✓] บันทึกต้น '{name}' ลงใน {zone_cfg['name']} เรียบร้อยแล้ว!")

def delete_plant():
    plants = list_plants()
    if not plants:
        return
        
    choice = input("\nระบุหมายเลขลำดับต้นไม้ที่ต้องการลบ (หรือกด Enter เพื่อยกเลิก): ").strip()
    if not choice:
        print("[!] ยกเลิกการลบ")
        return
        
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(plants):
            target = plants[idx]
            confirm = input(f"⚠️ ยืนยันการลบ '{target['name']}' ใน {target.get('zone_name', '')} หรือไม่? (y/n): ").strip().lower()
            if confirm == 'y':
                del plants[idx]
                data = load_json(PLANTS_FILE, {})
                data["plants"] = plants
                data["updated_at"] = datetime.now().isoformat()
                save_json(PLANTS_FILE, data)
                print(f"[✓] ลบ '{target['name']}' ออกจากระบบเรียบร้อยแล้ว!")
            else:
                print("[-] ยกเลิกการลบ")
        else:
            print("[!] ลำดับไม่ถูกต้อง")
    except ValueError:
        print("[!] กรุณาระบุเป็นตัวเลข")

def print_menu():
    print("\n" + "="*50)
    print(" 🌱 Garden Plan Management (ระบบจัดการแปลนต้นไม้)")
    print("="*50)
    print(" 1. แสดงรายการต้นไม้ทั้งหมดตามโซน")
    print(" 2. ➕ เพิ่มต้นไม้ใหม่ (ดึงข้อมูล/ภาพใบไม้อัตโนมัติ)")
    print(" 3. ❌ ลบต้นไม้")
    print(" 4. 🌐 เปิดดูหน้าเว็บ index.html ในเบราว์เซอร์")
    print(" 5. 🚀 สั่งรัน ~github_update.bat (อัปโหลดขึ้น GitHub)")
    print(" 0. ออกจากโปรแกรม")
    print("="*50)

def main():
    while True:
        print_menu()
        choice = input("เลือกเมนู (0-5): ").strip()
        if choice == "1":
            list_plants()
        elif choice == "2":
            add_plant()
        elif choice == "3":
            delete_plant()
        elif choice == "4":
            import webbrowser
            webbrowser.open(INDEX_HTML_FILE)
        elif choice == "5":
            bat_path = os.path.join(BASE_DIR, "~github_update.bat")
            if os.path.exists(bat_path):
                os.system(f'cmd /c "{bat_path}"')
            else:
                print("[!] ไม่พบไฟล์ ~github_update.bat")
        elif choice == "0":
            print("\nขอบคุณที่ใช้งานครับ สวัสดีครับ 👋")
            break
        else:
            print("[!] กรุณาเลือกตัวเลขเมนูที่ถูกต้อง")

if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n\nออกจากโปรแกรมเรียบร้อยครับ 👋")

