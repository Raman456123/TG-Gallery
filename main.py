import asyncio
import logging
from aiohttp import web
from streamer.client import app, logger as client_logger
from streamer.routes import routes
from streamer.config import HOST, PORT, PUBLIC_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def start_server():
    """Start the aiohttp server and Pyrogram client."""
    try:
        # Start Pyrogram client
        await app.start()
        me = await app.get_me()
        logger.info(f"✓ Logged in as: {me.first_name} (ID: {me.id})")
        
        if me.is_bot:
            logger.error("ERROR: Logged in as BOT instead of USER! Check TG_SESSION_STRING")
            return
        
        # Create aiohttp app
        web_app = web.Application()
        web_app.add_routes(routes)
        
        # Start web server
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, HOST, PORT)
        await site.start()
        
        logger.info(f"✓ Server started at http://{HOST}:{PORT}")
        logger.info(f"✓ Public URL: {PUBLIC_URL}")
        logger.info("✓ Ready to stream!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        try:
            if app.is_connected:
                await app.stop()
        except:
            pass  # Already stopped

if __name__ == "__main__":
    asyncio.run(start_server())
