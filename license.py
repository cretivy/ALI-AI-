import os
import sys
import json
import uuid
import platform
import hashlib
import requests
from datetime import datetime

SUPABASE_URL = "https://sqattjfwlghtdovzwunk.supabase.co"
SUPABASE_KEY = "sb_publishable_KHamdoKZrt_tj0T0VtFpmg_0_tYHwc3"
LICENSE_CACHE_FILE = os.path.expanduser("~/.munisa_license.json")

def get_hwid() -> str:
    """Generates a unique hardware fingerprint (HWID) for Mac & Windows"""
    raw_id = f"{uuid.getnode()}-{platform.processor()}-{platform.system()}"
    return hashlib.sha256(raw_id.encode('utf-8')).hexdigest()[:32]

def verify_license(license_key: str) -> tuple[bool, str]:
    """
    Validates license key against Supabase DB and binds to hardware ID (HWID).
    Returns (is_valid: bool, message: str)
    """
    if not license_key or not license_key.strip():
        return False, "Litsenziya kaliti kiritilmadi!"

    key = license_key.strip().upper()
    url = f"{SUPABASE_URL}/rest/v1/licenses?license_key=eq.{key}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return False, f"Serverga bog'lanishda xatolik ({r.status_code})"

        records = r.json()
        if not records:
            return False, "❌ Noto'g'ri litsenziya kaliti! Iltimos, qaytadan tekshiring."

        data = records[0]
        
        # 1. Check Status
        if data.get("status") != "active":
            return False, f"❌ Ushbu litsenziya faol emas! Holati: {data.get('status')}"

        # 2. Check Expiration Date
        expires_at_str = data.get("expires_at")
        if expires_at_str:
            # Parse ISO timestamp
            exp_date = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if datetime.now(exp_date.tzinfo) > exp_date:
                return False, f"❌ Ushbu litsenziya muddati tugagan! (Tugash sanasi: {exp_date.strftime('%Y-%m-%d')})"

        # 3. Check HWID Binding
        current_hwid = get_hwid()
        saved_hwid = data.get("hwid")

        if not saved_hwid:
            # First time activation: bind HWID to license key
            patch_url = f"{SUPABASE_URL}/rest/v1/licenses?id=eq.{data['id']}"
            requests.patch(patch_url, json={"hwid": current_hwid}, headers=headers, timeout=5)
        elif saved_hwid != current_hwid:
            return False, "❌ Ushbu litsenziya kaliti boshqa kompyuterga bog'langan!"

        # Cache valid license locally
        cache_data = {
            "license_key": key,
            "client_name": data.get("client_name"),
            "hwid": current_hwid,
            "expires_at": data.get("expires_at")
        }
        with open(LICENSE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return True, f"✅ Litsenziya tasdiqlandi! Xush kelibsiz, {data.get('client_name')}!"

    except Exception as e:
        return False, f"Litsenziya tekshirishda xatolik: {e}"

def check_saved_license() -> tuple[bool, str]:
    """Checks locally cached license file on app startup"""
    if not os.path.exists(LICENSE_CACHE_FILE):
        return False, "Litsenziya fayli topilmadi."

    try:
        with open(LICENSE_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)

        key = cache.get("license_key")
        if not key:
            return False, "Litsenziya keshda mavjud emas."

        # Re-verify online to prevent local tampering
        return verify_license(key)
    except Exception:
        return False, "Litsenziya keshini o'qishda xatolik."

if __name__ == "__main__":
    print("🔑 Litsenziya modulini sinash...")
    test_key = "MUNISA-TEST-1111-2026"
    valid, msg = verify_license(test_key)
    print(f"Natija: {valid} -> {msg}")
