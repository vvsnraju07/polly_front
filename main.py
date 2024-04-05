import asyncio
import aiobotocore.session
from fastapi import FastAPI, WebSocket
from pydantic_settings import BaseSettings
from functools import lru_cache
import io

app = FastAPI()

class Settings(BaseSettings):
    AWS_AK: str
    AWS_SAK: str
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

@app.websocket("/test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if data:
                await generate_and_send_audio(data, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")

async def generate_and_send_audio(text: str, websocket: WebSocket):
    aws_region = 'us-east-1'  # Set the AWS region explicitly
    
    session = aiobotocore.session.AioSession()
    async with session.create_client('polly',
                                      aws_access_key_id=get_settings().AWS_AK,
                                      aws_secret_access_key=get_settings().AWS_SAK,
                                      region_name=aws_region) as polly_client:
        response = await polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Raveena'
        )
        
        # Create an empty buffer to store the concatenated audio data
        audio_buffer = io.BytesIO()
        
        async for chunk in response['AudioStream'].iter_chunks():
            audio_buffer.write(chunk)
        
        # Get the concatenated audio data
        audio_data = audio_buffer.getvalue()
        
        # Send the entire audio data as a single chunk
        await websocket.send_bytes(audio_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
