import fastapi
import pathlib
import json
import uvicorn
from fastapi.middleware import cors
from fastapi import WebSocket, WebSocketDisconnect
import requests
import base64
from dotenv import load_dotenv
import os
import tempfile
import asyncio
import subprocess
import shutil
from spotify import SpotifyHandler

load_dotenv()

app = fastapi.FastAPI()
app.add_middleware(cors.CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- WebSocket manager (unverändert) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, userid: str, websocket: WebSocket):
        if userid not in self.active_connections:
            self.active_connections[userid] = set()
        self.active_connections[userid].add(websocket)
        return self.active_connections[userid]

    def disconnect(self, userid: str, websocket: WebSocket):
        if userid in self.active_connections:
            self.active_connections[userid].discard(websocket)
            if not self.active_connections[userid]:
                del self.active_connections[userid]

    async def send_presence(self, userid: str, presence: dict):
        if userid in self.active_connections:
            data = {"type": "presence_update", "userid": userid, "presence": presence}
            for ws in list(self.active_connections[userid]):
                try:
                    await ws.send_json(data)
                except Exception:
                    self.disconnect(userid, ws)

manager = ConnectionManager()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    userid = None
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            print(f"Received raw data: {data}")
            try:
                data = data.replace("'", '"')
                print(f"Received data after replace: {data}")
                data = json.loads(data)
            except json.JSONDecodeError as e:
                await websocket.send_text("Invalid JSON format: " + str(e))
                continue
            print(f"Received json data: {data}")
            print(data.get("type"))
            if data.get("type") == "connect":
                userid = data.get("userid")
                if not userid:
                    await websocket.send_text("Missing 'userid' in connect payload.")
                    continue

                print(f"Connecting user {userid}...")
                await manager.connect(userid, websocket)
                print(f"User {userid} connected. Active connections: {len(manager.active_connections.get(userid, []))}")
                try:
                    with open(pathlib.Path(__file__).parent / "presences.json") as f:
                        presences = json.load(f)
                except Exception as e:
                    await websocket.send_text("Error loading presences: " + str(e))
                    presences = {}

                presence = presences.get(userid)
                print(f"Sending presence to {userid}")
                await websocket.send_json({
                    "type": "connected",
                    "userid": userid,
                    "presence": presence
                })

            else:
                await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        print(f"User {userid} disconnected.")
        if userid:
            manager.disconnect(userid, websocket)
    except Exception:
        print(f"Error with user {userid}: {userid}")
        if userid:
            manager.disconnect(userid, websocket)

@app.get("/")
async def get_index():
    return fastapi.responses.RedirectResponse(url="/presence")

@app.get("/presence/handler.js")
async def get_handler_js():
    return fastapi.responses.FileResponse(pathlib.Path(__file__).parent / "handler.js")        

@app.get("/presence/imagenotfound.png")
async def get_image_not_found():
    return fastapi.responses.FileResponse(pathlib.Path(__file__).parent / "assets/404cat.png")

@app.get("/presence")
async def get_presence():
    return fastapi.responses.JSONResponse({
        "status": "ok",
        "message": "Presence API is running. Use /presence/{userid} to access presence.",
        "getbanner": "Use /presence/{userid}/banner to get the user's banner.",
        "get avatar": "Use /presence/{userid}/avatar to get the user's avatar.",
        "get json": "Use /presence/{userid}/json to get the user's presence in JSON format.",
        "screenshot_engine": "Ultra-fast wkhtmltoimage + Chrome headless"
    })

@app.get("/presence/{userid}")
async def get_presence_detail(userid: str):
    iframe_headers = {
        "Content-Security-Policy": "frame-ancestors 'self' *;",
        "X-Frame-Options": "ALLOWALL"
    }
    return fastapi.responses.FileResponse(pathlib.Path(__file__).parent / "presence.html", headers=iframe_headers)


@app.get("/presence/videos/clips/{trackid}")
async def get_song_video_clip(trackid: str):
    handler = SpotifyHandler(os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET"))
    video_info = handler.get_song_video(trackid)
    if video_info and video_info.get("downloaded_file"):
        return fastapi.responses.FileResponse(video_info["downloaded_file"], media_type="video/mp4", filename=f"{trackid}_clip.mp4")
    else:
        raise fastapi.HTTPException(status_code=404, detail="Video clip not found")


@app.get("/presence/{userid}/image")
async def get_presence_image(userid: str):
    """Screenshot-Generierung mit Siteshot API"""
    try:
        # Siteshot API verwenden
        target_url = f"https://api.deutscher775.de/presence/{userid}?imgdims"
        screenshotlayer_url = f"https://api.screenshotlayer.com/api/capture?" \
                            f"access_key={os.getenv('SCREENSHOTLAYER_API_KEY')}" \
                            f"&url={target_url}" \
                            f"&viewport=350x130" \
                            f"&width=350"



        response = requests.get(screenshotlayer_url, timeout=10)
        print(f"Response from screenshotlayer: {response.status_code} - {response.text}")

        if response.ok:
            # Temporäre Datei erstellen
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            return fastapi.responses.FileResponse(
                path=temp_path
            )
        else:
            print(f"Screenshotlayer API failed with status {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Screenshotlayer API failed: {e}")
    
    return fastapi.responses.JSONResponse(
        {"error": "Screenshot generation failed"}
    )

# --- Restliche Endpoints unverändert ---
@app.get("/presence/status_icons/{status}")
async def get_status_icon(status: str):
    if status not in ["online.png", "idle.png", "dnd.png", "offline.png"]:
        raise fastapi.HTTPException(status_code=404, detail="Status icon not found")
    return fastapi.responses.FileResponse(pathlib.Path(__file__).parent / "status_icons" / f"{status}")

@app.get("/presence/{userid}/banner")
async def get_banner(userid: str):
    presences_file = open(pathlib.Path(__file__).parent / "presences.json")
    presences = json.load(presences_file)
    presences_file.close()
    presence = presences.get(userid, {})
    banner_url = presence.get("banner")
    if not banner_url:
        raise fastapi.HTTPException(status_code=404, detail="Banner not found")
    return fastapi.responses.JSONResponse({"banner": banner_url})

@app.get("/presence/{userid}/avatar")
async def get_avatar(userid: str):
    presences_file = open(pathlib.Path(__file__).parent / "presences.json")
    presences = json.load(presences_file)
    presences_file.close()
    presence = presences.get(userid, {})
    avatar_url = presence.get("avatar")
    if not avatar_url:
        raise fastapi.HTTPException(status_code=404, detail="Avatar not found")
    return fastapi.responses.JSONResponse({"avatar": avatar_url})

@app.get("/presence/{userid}/json")
async def get_presence_json(userid: str):
    presences_file = open(pathlib.Path(__file__).parent / "presences.json")
    presences = json.load(presences_file)
    presences_file.close()
    presence = presences.get(userid, {})
    if not presence:
        raise fastapi.HTTPException(status_code=404, detail="Presence not found")
    return fastapi.responses.JSONResponse(presence)

@app.post("/presence/{userid}")
async def set_presence(userid: str, request: fastapi.Request):
    presence = await request.json()
    presences_file = open(pathlib.Path(__file__).parent / "presences.json")
    presences = json.load(presences_file)
    presences_file.close()
    presences[userid] = presence

    avatar_url = presence.get("avatar")
    if avatar_url:
        try:
            r = requests.get(avatar_url, timeout=10)
            if r.status_code == 200:
                content_type = r.headers.get("Content-Type", "image/png")
                presence["avatar"] = f"data:{content_type};base64,{base64.b64encode(r.content).decode('utf-8')}"
        except Exception:
            pass

    banner_url = presence.get("banner")
    if banner_url:
        try:
            r = requests.get(banner_url, timeout=10)
            if r.status_code == 200:
                content_type = r.headers.get("Content-Type", "image/png")
                presence["banner"] = f"data:{content_type};base64,{base64.b64encode(r.content).decode('utf-8')}"
        except Exception:
            pass

    presences_file = open(pathlib.Path(__file__).parent / "presences.json", "w")
    json.dump(presences, presences_file, indent=4)
    presences_file.close()

    # Broadcast update to WebSocket clients
    if int(userid) in manager.active_connections.keys() or userid in manager.active_connections.keys():
        await manager.send_presence(userid, presence)
    else:
        print(f"Warning: No active connections found for userid {userid}")

    return {"status": "success"}

if __name__ == "__main__":
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '8000'))
    uvicorn.run(app, host=host, port=port, log_level="info")
