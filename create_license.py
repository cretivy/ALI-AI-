import sys
import random
import string
import requests
from datetime import datetime, timedelta

SUPABASE_URL = "https://sqattjfwlghtdovzwunk.supabase.co"
SUPABASE_KEY = "sb_publishable_KHamdoKZrt_tj0T0VtFpmg_0_tYHwc3"

def generate_license(client_name: str, days: int = 30) -> str:
    """Generates a new unique license key and saves it to Supabase"""
    random_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    license_key = f"MUNISA-{random_code}"
    
    expires_at = (datetime.now() + timedelta(days=days)).isoformat()
    
    url = f"{SUPABASE_URL}/rest/v1/licenses"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {
        "license_key": license_key,
        "client_name": client_name,
        "expires_at": expires_at,
        "status": "active"
    }
    
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code in [200, 201]:
        print(f"\n🎉 YANGI LITSENZIYA TAYYORLANTI!")
        print(f"👤 Mijoz: {client_name}")
        print(f"🔑 Litsenziya Kaliti: {license_key}")
        print(f"📅 Muddati: {days} kun ({expires_at[:10]} gacha)")
        print("-" * 45)
        return license_key
    else:
        print(f"❌ Xatolik: {r.status_code} -> {r.text}")
        return ""

if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        generate_license(name, days)
    else:
        name = input("👤 Mijoz ismini kiriting: ").strip() or "Mijoz 1"
        days_str = input("📅 Necha kunga berilsin? (Standart: 30): ").strip()
        days = int(days_str) if days_str.isdigit() else 30
        generate_license(name, days)
