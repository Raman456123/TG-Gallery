import logging
from pyrogram import Client
from .config import API_ID, API_HASH, SESSION_STRING

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Pyrogram client with session string (Userbot mode)
app = Client(
    name="tg_gallery_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True  # Don't create session files
)

logger.info("✓ Pyrogram client initialized")
