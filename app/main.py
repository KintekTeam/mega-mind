from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from typing import Dict, Set
import uvicorn
from datetime import datetime

app = FastAPI(title="Mega Mind Support Platform")

class ConnectionManager:
    def __init__(self):
        self.sessions: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.sessions:
            self.sessions[session_id] = set()
            print(f"[{datetime.now()}] New session created: {session_id}")
        self.sessions[session_id].add(websocket)
        print(f"[{datetime.now()}] Client connected to session {session_id}")
        print(f"Active sessions: {list(self.sessions.keys())}")
        
    async def disconnect(self, websocket: WebSocket, session_id: str):
        self.sessions[session_id].remove(websocket)
        print(f"[{datetime.now()}] Client disconnected from session {session_id}")
        if not self.sessions[session_id]:
            del self.sessions[session_id]
            print(f"[{datetime.now()}] Session {session_id} closed - no more clients")
        print(f"Active sessions: {list(self.sessions.keys())}")
            
    async def send_message(self, message: str, session_id: str, sender: WebSocket):
        if session_id in self.sessions:
            print(f"[{datetime.now()}] Broadcasting in session {session_id}: {message}")
            for connection in self.sessions[session_id]:
                if connection != sender:
                    await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    return {
        "status": "Mega Mind Support Platform is running",
        "version": "0.1.0"
    }

@app.get("/test", response_class=HTMLResponse)
async def get_test_client():
    with open('test_client.html') as f:
        return f.read()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[{datetime.now()}] Session {session_id} received: {data}")
            await manager.send_message(data, session_id, websocket)
    except Exception as e:
        print(f"[{datetime.now()}] Error in session {session_id}: {e}")
        await manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)