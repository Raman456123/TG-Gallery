import logging
from aiohttp import web
from .client import app
from .config import PUBLIC_URL

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


def parse_channel_input(channel_input: str):
    """
    Parse channel input - can be username, URL, invite link, or numeric ID.
    
    Examples:
        - "channelname" -> "channelname"
        - "@channelname" -> "channelname"
        - "https://t.me/channelname" -> "channelname"
        - "https://t.me/c/1234567890" -> -1001234567890 (private channel)
        - "https://t.me/+AbCd123" -> "https://t.me/+AbCd123" (invite link)
        - "t.me/+AbCd123" -> "https://t.me/+AbCd123" (invite link)
        - "-1001234567890" -> -1001234567890
    """
    channel_input = channel_input.strip()
    
    # Remove @ prefix if present
    if channel_input.startswith("@"):
        return channel_input[1:]
    
    # Handle t.me URLs
    if "t.me/" in channel_input:
        # Extract the part after t.me/
        parts = channel_input.split("t.me/")[-1].split("/")
        
        # Invite link format: t.me/+hash or t.me/joinchat/hash
        if parts[0].startswith("+") or parts[0] == "joinchat":
            # Return full invite URL (Pyrogram can handle this)
            if not channel_input.startswith("http"):
                return f"https://t.me/{parts[0]}" if parts[0].startswith("+") else f"https://t.me/{'/'.join(parts[:2])}"
            return channel_input.split("?")[0]  # Remove query params
        
        # Private channel URL: t.me/c/1234567890
        if parts[0] == "c" and len(parts) > 1:
            channel_id = parts[1].split("?")[0]  # Remove query params
            # Convert to proper peer ID format (-100 prefix)
            return int(f"-100{channel_id}")
        
        # Public channel URL: t.me/channelname
        return parts[0].split("?")[0]  # Remove query params
    
    # Try as numeric ID
    try:
        return int(channel_input)
    except ValueError:
        # Regular username
        return channel_input

@routes.get("/api/list")
async def list_channel_files(request):
    """List media files from a Telegram channel."""
    try:
        channel_input = request.query.get("channel")
        if not channel_input:
            return web.json_response({"error": "Missing 'channel' parameter"}, status=400)
        
        limit = int(request.query.get("limit", 50))
        offset_id = int(request.query.get("offset_id", 0))
        
        # Parse channel input (username, URL, or ID)
        channel = parse_channel_input(channel_input)
        logger.info(f"[LIST] Input: {channel_input} -> Parsed: {channel}")
        
        # Get channel entity
        try:
            entity = await app.get_chat(channel)
            chat_id = entity.id
        except Exception as e:
            logger.error(f"Channel not found: {channel} - {e}")
            return web.json_response({"error": f"Channel not found: {str(e)}"}, status=404)
        
        files = []
        async for message in app.get_chat_history(chat_id, limit=limit, offset_id=offset_id):
            if not message.media:
                continue
            
            # Determine media type and file info
            media_type = "document"
            file_name = f"file_{message.id}"
            file_size = 0
            mime_type = "application/octet-stream"
            
            # Extract media-specific metadata
            width = height = duration = None
            
            if message.photo:
                media_type = "photo"
                file_size = message.photo.file_size
                mime_type = "image/jpeg"
                file_name = f"photo_{message.id}.jpg"
                # Get largest photo size for dimensions
                largest = max(message.photo.thumbs, key=lambda x: x.file_size) if message.photo.thumbs else None
                if largest:
                    width = largest.width
                    height = largest.height
            elif message.video:
                media_type = "video"
                file_size = message.video.file_size
                mime_type = message.video.mime_type or "video/mp4"
                file_name = message.video.file_name or f"video_{message.id}.mp4"
                width = message.video.width
                height = message.video.height
                duration = message.video.duration
            elif message.document:
                media_type = "document"
                file_size = message.document.file_size
                mime_type = message.document.mime_type or "application/octet-stream"
                file_name = message.document.file_name or f"document_{message.id}"
            elif message.audio:
                media_type = "audio"
                file_size = message.audio.file_size
                mime_type = message.audio.mime_type or "audio/mpeg"
                file_name = message.audio.file_name or f"audio_{message.id}.mp3"
                duration = message.audio.duration
            
            # Generate stream URL using the request's host (so it works from Android app)
            # If accessing from 10.124.150.52, stream URL will use 10.124.150.52
            # If accessing from localhost, stream URL will use localhost
            request_host = request.headers.get('Host', 'localhost:8000')
            base_url = f"http://{request_host}"
            stream_url = f"{base_url}/stream?channel={channel_input}&message_id={message.id}&filename={file_name}"
            
            # Build file info with all metadata
            file_info = {
                "id": message.id,
                "name": file_name,
                "size": file_size,
                "type": media_type,
                "mime_type": mime_type,
                "stream_url": stream_url,
                "caption": message.caption or "",
                "date": int(message.date.timestamp()),  # Unix timestamp
            }
            
            # Add optional fields if available
            if width:
                file_info["width"] = width
            if height:
                file_info["height"] = height
            if duration:
                file_info["duration"] = duration
            if message.views:
                file_info["views"] = message.views
            
            files.append(file_info)
        
        return web.json_response({"files": files})
    
    except Exception as e:
        logger.error(f"Error listing files: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)


@routes.get("/stream")
async def stream_file(request):
    """Stream a file from Telegram using channel username."""
    try:
        channel_input = request.query.get("channel")
        message_id = int(request.query.get("message_id"))
        filename = request.query.get("filename")
        
        if not channel_input or not message_id:
            return web.Response(status=400, text="Missing parameters")
        
        # Parse channel input
        channel = parse_channel_input(channel_input)
        logger.info(f"[STREAM] Input: {channel_input} -> Parsed: {channel}, msg={message_id}")
        
        # Resolve channel to get chat_id
        try:
            entity = await app.get_chat(channel)
            chat_id = entity.id
            logger.info(f"[STREAM] Resolved to chat_id={chat_id}")
        except Exception as e:
            logger.error(f"[STREAM] Channel not found: {e}")
            return web.Response(status=404, text=f"Channel not found: {str(e)}")
        
        # Get the message
        message = await app.get_messages(chat_id, message_id)
        if not message or not message.media:
            logger.error("[STREAM] Message not found or no media")
            return web.Response(status=404, text="File not found")
        
        logger.info(f"[STREAM] Message found: {type(message.media)}")
        
        # Get file properties
        if message.photo:
            file_size = message.photo.file_size
            mime_type = "image/jpeg"
        elif message.video:
            file_size = message.video.file_size
            mime_type = message.video.mime_type or "video/mp4"
        elif message.document:
            file_size = message.document.file_size
            mime_type = message.document.mime_type or "application/octet-stream"
        elif message.audio:
            file_size = message.audio.file_size
            mime_type = message.audio.mime_type or "audio/mpeg"
        else:
            return web.Response(status=404, text="Unsupported media type")
        
        logger.info(f"[STREAM] size={file_size}, mime={mime_type}")
        
        # Parse range header
        range_header = request.headers.get("Range", "")
        if range_header:
            range_value = range_header.replace("bytes=", "")
            parts = range_value.split("-")
            offset = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        else:
            offset = 0
            end = file_size - 1
        
        limit = end - offset + 1
        logger.info(f"[STREAM] offset={offset}, end={end}, limit={limit}")
        
        # Stream using custom helper
        async def file_stream():
            try:
                logger.info("[STREAM] Starting custom stream...")
                # Import here to avoid circular import
                from .stream_helper import stream_file as stream_file_helper
                
                bytes_sent = 0
                async for chunk in stream_file_helper(app, message, offset=offset, limit=limit):
                    yield chunk
                    bytes_sent += len(chunk)
                
                logger.info(f"[STREAM] Complete: {bytes_sent} bytes")
                    
            except Exception as e:
                logger.error(f"[STREAM] ERROR: {e}", exc_info=True)
                raise
        
        # Response headers
        headers = {
            "Content-Type": mime_type,
            "Content-Length": str(limit),
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{filename}"'
        }
        
        if range_header:
            headers["Content-Range"] = f"bytes {offset}-{end}/{file_size}"
            status = 206
        else:
            status = 200
        
        logger.info(f"[STREAM] Response: status={status}")
        
        return web.Response(
            status=status,
            headers=headers,
            body=file_stream()
        )
    
    except Exception as e:
        logger.error(f"[STREAM] FATAL: {e}", exc_info=True)
        return web.Response(status=500, text=str(e))
