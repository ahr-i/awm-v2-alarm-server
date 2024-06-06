import uvicorn
from fastapi import FastAPI, WebSocket, Request
from app.connection_server import ConnectionServer
import json

app = FastAPI()
manager = ConnectionServer()

# 디바이스간 연결 소켓 설정
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket=websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg["type"] == "register":
                device_id = msg["deviceId"]
                print(f"Connected With {device_id}")
                await manager.update_active(websocket=websocket, device_id=device_id)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(websocket=websocket)


# 백엔드 요청 설정
@app.post("/verify/")
async def verify_request(request: Request):
    data = await request.json()
    latitude = data["latitude"]
    longitude = data["longitude"]
    location_id = data["location_id"]

    await manager.send_verify_message(location_id=location_id, latitude=latitude, longitude=longitude)
    return {"status": "Successed"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3075)
