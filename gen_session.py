from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Get these from my.telegram.org
API_ID = int(input("Enter API ID: "))
API_HASH = input("Enter API HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n--- COPY THE STRING BELOW ---")
    print(client.session.save())
    print("--- END ---")
    print("\nPaste this string into your Koyeb Environment Variables as 'TG_SESSION_STRING'.")
