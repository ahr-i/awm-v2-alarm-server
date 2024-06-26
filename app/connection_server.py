from fastapi import FastAPI, WebSocket
import redis
from typing import List, Tuple
import random
import json
class ConnectionServer:
    def __init__(self):
        self.active_connections: List[Tuple] = []
        try:
            self.redis_client = redis.Redis(
                host='vocal-dragon-43557.upstash.io',
                port=6379,
                password="AaolAAIncDFkN2NkODRhMmFiNmM0NDg1OTBhMzY3M2NlOTI5M2EzNXAxNDM1NTc",
                ssl=True
            )
            print(" - Success to connect in Redis - ")
        except:
            print(" - Failed to connect in Redis - ")
        print(f"Active Connections: {len(self.active_connections)}" )
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
    def disconnect(self, websocket: WebSocket):
        self.active_connections = [(conn, dev_id) for conn, dev_id in self.active_connections if conn != websocket]
    async def update_active(self, websocket, device_id: str):
        self.active_connections.append((websocket, device_id))
        print(f"Active Connections: {len(self.active_connections)}" )
        
    # 근처에 있는 디바이스의 id를 반환
    async def request_nearby_device(self, latitude: str, longitude: str) -> List[str]:
        latitude = float(latitude)
        longitude = float(longitude)
        rounded_key = self.get_rounded_key(latitude=latitude, longitude=longitude)
        print(f"[DEBUG] Rounded Key From Client: {rounded_key}")
        matching_keys = self.find_matching_keys(rounded_key=rounded_key)
        device_ids = []
        for key in matching_keys:
            devices = self.redis_client.lrange(key,0,-1)
            device_ids.extend(devices)
        return [device_id.decode('utf-8') for device_id in device_ids]

    def get_rounded_key(self, latitude: float, longitude: float) -> str:
        lat = round(latitude,3)
        formatted_lat = "{:.3f}".format(lat)
        long = round(longitude,3)
        formatted_long = "{:.3f}".format(long)
        return f"{formatted_lat},{formatted_long}"
    
    # 모든 키를 참조한 뒤, 반올림 했을 때 업데이트된 장소의 좌표값과 일치하는 좌표값을 반환
    def find_matching_keys(self, rounded_key: str) -> List[str]:
        matching_keys = []
        keys = self.redis_client.scan_iter()
        for key in keys:
            decoded_key = key.decode('utf-8')
            print(f"[DEBUG] decoded Key: {decoded_key}")
            
            if decoded_key.startswith("weather:"):
                decoded_key = decoded_key.split(':')[1]
            
            latitude, longitude = map(float, decoded_key.split(','))
            candidate = self.get_rounded_key(latitude=latitude, longitude=longitude)
            # print(f"[DEBUG] Candidate = {candidate}")
            if candidate == rounded_key:
                # print(f"[DEBUG] Matching Key: {decoded_key}")
                matching_keys.append(decoded_key)
        return matching_keys
    
    async def send_verify_message(self, location_id: str, latitude: str, longitude: str):
        # redis에서 좌표에서 가까운 디바이스의 주소를 가져오기
        number_of_sample = 10   
        device_ids = await self.request_nearby_device(latitude=latitude, longitude=longitude)
        # 샘플 숫자만큼 메시지를 보내기
        if device_ids:
            selected_device_ids = random.sample(device_ids, min(number_of_sample, len(device_ids)))
            print("selected devices: ",len(selected_device_ids))
            # 선택된 디바이스 ID와 Manager에서 관리중인 (Connection, device_id)를 비교하여, 서로의 device_id가 일치하다면 해당 디바이스와 연결된 소켓 객체를 통해 메시지를 보냄. 
            for selected_device_id in selected_device_ids:
                websocket = None
                for conn, dev_id in self.active_connections:
                    print(f"[DEBUG] Checking dev_id: {dev_id}")
                    if dev_id == selected_device_id:
                        websocket = conn
                        break
                print(f"[DEBUG] device ID: {selected_device_id}")
                if websocket:
                    print(f"[DEBUG] Websocket Selected, ID: {selected_device_id}")
                    await self.send_message(websocket=websocket, msg_type="verfiy", message="근처 장소의 정보가 새로 업데이트 되었습니다!\n확인해주세요!", location_id=location_id, selected_device=selected_device_id)
    async def send_message(self, websocket: WebSocket, msg_type: str, message: str, location_id: str, selected_device: str):
        data = {
            "selected_device": selected_device,
            "type": msg_type,
            "location_id": location_id,
            "message": message
        }
        await websocket.send_json(data)
        print("[Socket Server] Socket Server send the notification signal!");
        
        
        
