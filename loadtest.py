import asyncio

import numpy as np
import websockets
import soundfile as sf

active_connections_bytes = {"bytes_sent": 0, "bytes_received": 0}


async def audio_client():
    try:
        async with websockets.connect('ws://3.95.56.144:8000/ws/audio', ping_interval=5000) as websocket:
            # Read the audio file data
            audio_data, sample_rate = sf.read('sample.wav')

            # Set the audio buffer size and calculate the total number of buffers
            buffer_size = 1024
            num_buffers = len(audio_data) // buffer_size

            # Send the audio data in fixed-size buffers
            for i in range(num_buffers):
                audio_buffer = audio_data[i * buffer_size:(i + 1) * buffer_size].tobytes()
                await websocket.send(audio_buffer)
                active_connections_bytes["bytes_sent"] += len(audio_buffer)

            # Receive and process audio data from the WebSocket endpoint
            while True:
                audio_data = await websocket.recv()
                active_connections_bytes["bytes_received"] += len(audio_data.encode("utf-8"))
                print(f'Received Message: {audio_data}.')
    except Exception:
        print(active_connections_bytes)


async def main():
    tasks = [asyncio.create_task(audio_client()) for _ in range(2)]
    await asyncio.gather(*tasks)


asyncio.run(main())
