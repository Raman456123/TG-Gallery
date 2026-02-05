import math
import logging
from pyrogram import Client, raw
from pyrogram.file_id import FileId

logger = logging.getLogger(__name__)

class StreamSession:
    """Handles file streaming from Telegram using Pyrogram."""
    
    def __init__(self, client: Client):
        self.client = client
        self.media_sessions = {}
    
    async def get_file_properties(self, chat_id: int, message_id: int):
        """Get file properties for a message."""
        try:
            message = await self.client.get_messages(chat_id, message_id)
            if not message or not message.media:
                return None
            
            # Get file_id from media
            media = message.media
            if hasattr(media, 'photo'):
                file_id_str = message.photo.file_id
            elif hasattr(media, 'video'):
                file_id_str = message.video.file_id
            elif hasattr(media, 'document'):
                file_id_str = message.document.file_id
            elif hasattr(media, 'audio'):
                file_id_str = message.audio.file_id
            else:
                return None
            
            # Decode file_id to get properties
            file_id = FileId.decode(file_id_str)
            
            return {
                'file_id': file_id,
                'file_size': message.document.file_size if message.document else (message.video.file_size if message.video else 0),
                'mime_type': message.document.mime_type if message.document else (message.video.mime_type if message.video else 'application/octet-stream'),
                'file_name': message.document.file_name if message.document else (message.video.file_name if message.video else f"file_{message_id}")
            }
        except Exception as e:
            logger.error(f"Error getting file properties: {e}")
            return None
    
    async def stream_file(self, file_id: FileId, offset: int, limit: int):
        """Stream file bytes using Pyrogram."""
        try:
            chunk_size = 1024 * 1024  # 1MB chunks
            current_offset = offset
            bytes_remaining = limit
            
            while bytes_remaining > 0:
                # Calculate chunk to request
                request_size = min(chunk_size, bytes_remaining)
                
                # Use Pyrogram's download_media with custom range
                # Note: Pyrogram handles the low-level GetFile requests internally
                async for chunk in self.client.stream_media(
                    file_id,
                    offset=current_offset,
                    limit=request_size
                ):
                    if not chunk:
                        break
                    
                    # Yield only what we need
                    if len(chunk) > bytes_remaining:
                        chunk = chunk[:bytes_remaining]
                    
                    yield chunk
                    
                    chunk_len = len(chunk)
                    bytes_remaining -= chunk_len
                    current_offset += chunk_len
                    
                    if bytes_remaining <= 0:
                        break
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
