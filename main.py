import boto3
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from functools import lru_cache  # Import lru_cache here
from pydantic_settings import BaseSettings

app = FastAPI()

class Settings(BaseSettings):
    AWS_AK:str
    AWS_SAK:str
    
    class Config:
        env_file=".env"

class Text(BaseModel):
    content: str
    output: str = "MP3"

@ app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if data:
                audio_data = await get_audio(data)
                await websocket.send_bytes(audio_data)
    except Exception as e:
        print(f"WebSocket error: {e}")

@ lru_cache()  # Decorate the function with lru_cache
def get_settings():
    return Settings()

async def get_audio(text: str) -> bytes:
    aws_region = 'us-east-1'  # Set the AWS region explicitly
    polly_client = boto3.client('polly', 
                                aws_access_key_id=get_settings().AWS_AK,
                                aws_secret_access_key=get_settings().AWS_SAK, 
                                region_name=aws_region)  # Use explicitly set region
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId='Raveena'
    )
    # Get the audio stream from the response
    audio_stream = response['AudioStream'].read()
    return audio_stream

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
