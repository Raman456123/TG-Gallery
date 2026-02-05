"""
Custom file streaming utilities for Pyrogram.
Adapted from TG-FileStreamBot for simpler implementation.
"""
import logging
from pyrogram import Client, raw,utils
from pyrogram.file_id import FileId

logger = logging.getLogger(__name__)

async def stream_file(client: Client, message, offset: int = 0, limit: int = 0):
    """
    Stream a file from Telegram in chunks.
    
    Args:
        client: Pyrogram client
        message: Message object containing media
        offset: Starting byte offset
        limit: Number of bytes to stream (0 = entire file)
    
    Yields:
        bytes: File chunks
    """
    # Get file_id from message media
    if message.photo:
        file_id_str = message.photo.file_id
    elif message.video:
        file_id_str = message.video.file_id
    elif message.document:
        file_id_str = message.document.file_id
    elif message.audio:
        file_id_str = message.audio.file_id
    else:
        raise ValueError("Message has no supported media")
    
    # Decode file_id
    file_id = FileId.decode(file_id_str)
    
    # Get file location
    location = get_file_location(file_id)
    
    # Stream chunks
    chunk_size = 512 * 1024  # 512KB per chunk
    current_offset = offset
    bytes_remaining = limit if limit > 0 else float('inf')
    
    while bytes_remaining > 0:
        # Request chunk from Telegram
        request_size = min(chunk_size, bytes_remaining) if bytes_remaining != float('inf') else chunk_size
        
        try:
            r = await client.invoke(
                raw.functions.upload.GetFile(
                    location=location,
                    offset=current_offset,
                    limit=chunk_size  # Always request full chunk, trim later
                )
            )
            
            if isinstance(r, raw.types.upload.File):
                chunk = r.bytes
                if not chunk:
                    break
                
                # Trim chunk if needed
                if limit > 0 and len(chunk) > bytes_remaining:
                    chunk = chunk[:int(bytes_remaining)]
                
                yield chunk
                
                current_offset += len(chunk)
                if limit > 0:
                    bytes_remaining -= len(chunk)
            else:
                break
                
        except Exception as e:
            logger.error(f"Error fetching chunk at offset {current_offset}: {e}")
            break


def get_file_location(file_id: FileId):
    """Get Telegram file location from FileId."""
    from pyrogram.file_id import FileType
    
    file_type = file_id.file_type
    
    if file_type == FileType.PHOTO:
        location = raw.types.InputPhotoFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size
        )
    else:  # Document, video, audio
        location = raw.types.InputDocumentFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size
        )
    
    return location
