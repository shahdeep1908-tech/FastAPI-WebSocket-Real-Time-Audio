import asyncio
import uuid
from datetime import datetime, timezone
from typing import List

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class WebSocketConnectionModel:
    user_id: str
    account_id: int
    socket: WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocketConnectionModel] = []
        self.bytes_sent = 0
        self.bytes_received = 0

    async def connect(self, account_id: int, user_id: str, websocket: WebSocket):
        await websocket.accept()
        connection = WebSocketConnectionModel()
        connection.account_id = account_id
        connection.user_id = user_id
        connection.socket = websocket
        connection.connection_date_time_utc = datetime.now(timezone.utc)
        self.active_connections.append(connection)
        return connection

    def disconnect(self, connection):
        self.active_connections.remove(connection)
        print(connection.user_id, f"bytes_sent: {self.bytes_sent}, bytes_received: {self.bytes_received}")

    async def send_personal_message(self):
        message = 'This is sound received'
        self.bytes_sent += len(message.encode("utf-8"))
        for connection in self.active_connections:
            await connection.socket.send_text(message)

    async def receive_message(self, connection) -> str:
        message = await connection.socket.receive_bytes()
        self.bytes_received += len(message)
        # await asyncio.sleep(0.1)  # add sleep to prevent CPU usage from spiking
        return message


manager = ConnectionManager()
# message_queue = asyncio.Queue()  # create a queue for processing messages


@app.get("/")
def read_root():
    return {"Hello": "World"}


async def process_messages(data):
    await asyncio.sleep(0.1)
    await manager.send_personal_message()


@app.websocket("/ws/audio")
async def audio_ws(websocket: WebSocket):
    # j = 1
    connection = await manager.connect(account_id=1, user_id=str(uuid.uuid4()), websocket=websocket)
    print('connection', connection.user_id)

    # if message_queue.empty():
    #     asyncio.create_task(process_messages())  # create task for processing messages

    try:
        while True:
            data = await manager.receive_message(connection=connection)
            # await asyncio.sleep(0)
            with open("Logs/cpu_usage.txt", "a") as f:
                f.write(f"{psutil.cpu_percent()}%\n")
            with open("Logs/virtual_memory.txt", "a") as f:
                f.write(f"{psutil.disk_usage('/').percent}%\n")
            with open("Logs/disk_usage.txt", "a") as f:
                f.write(f"{psutil.virtual_memory().percent}%\n")
            asyncio.create_task(process_messages(data))
            # message_queue.put_nowait(data)  # put message in queue
            # j += 1

    except (WebSocketDisconnect, Exception):
        print('connection closed', connection.user_id)
        manager.disconnect(connection=connection)
