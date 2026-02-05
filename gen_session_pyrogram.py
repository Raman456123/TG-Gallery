"""
Generate Pyrogram Session String for TG Gallery Bot
Run this script to generate a session string for Pyrogram (not Telethon).
"""
from pyrogram import Client

# Get these from my.telegram.org
API_ID = int(input("Enter API ID: "))
API_HASH = input("Enter API HASH: ")

print("\n🔐 Generating Pyrogram session string...")
print("⚠️  You'll receive a code on Telegram - enter it when prompted\n")

# Create a temporary client to generate session
app = Client(
    name="tg_gallery_session",
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True
)

async def generate_session():
    await app.start()
    session_string = await app.export_session_string()
    
    print("\n" + "="*60)
    print("✅ SESSION STRING GENERATED!")
    print("="*60)
    print("\n📋 COPY THE STRING BELOW (everything between the lines):\n")
    print("-" * 60)
    print(session_string)
    print("-" * 60)
    print("\n📝 Paste this into your .env file as:")
    print(f"TG_SESSION_STRING={session_string}")
    print("\n⚠️  Keep this private! Don't share it with anyone!")
    print("="*60)
    
    await app.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_session())
