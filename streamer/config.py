import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Telegram API Credentials
API_ID = int(os.environ.get("TG_API_ID", 0))
API_HASH = os.environ.get("TG_API_HASH", "")
SESSION_STRING = os.environ.get("TG_SESSION_STRING", "")

if not API_ID or not API_HASH:
    print("ERROR: TG_API_ID and TG_API_HASH must be set")
    sys.exit(1)

if not SESSION_STRING:
    print("ERROR: TG_SESSION_STRING must be set for Userbot mode")
    sys.exit(1)

# Validate session string (should be base64-like, quite long)
if len(SESSION_STRING) < 200:
    print(f"ERROR: TG_SESSION_STRING seems too short ({len(SESSION_STRING)} chars). Expected 300+ characters.")
    print("Make sure you copied the full session string from gen_session.py")
    sys.exit(1)

# Server Config
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
PUBLIC_URL = os.environ.get("PUBLIC_URL", f"http://{HOST}:{PORT}")

# Ensure PUBLIC_URL doesn't have trailing slash
if PUBLIC_URL.endswith("/"):
    PUBLIC_URL = PUBLIC_URL[:-1]

print(f"✓ Config loaded: API_ID={API_ID}, PORT={PORT}")
print(f"✓ Public URL: {PUBLIC_URL}")
