from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from config.auth_router import auth_router
from models.drivers import LocationUpdate
from config.database import locations_collection
from datetime import datetime

app = FastAPI()
app.include_router(auth_router)

connected_clients = {}

@app.websocket("/ws/location/{driver_id}")
async def websocket_location(websocket: WebSocket, driver_id: str):
    await websocket.accept()
    connected_clients[driver_id] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            data["driver_id"] = driver_id
            data["timestamp"] = datetime.utcnow()
            locations_collection.insert_one(data)
            # Optionally broadcast to all users or return to sender
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        connected_clients.pop(driver_id, None)
