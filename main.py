import asyncio

from fastapi import FastAPI

from media.media_manager import MediaManager

app = FastAPI()

manager: MediaManager


@app.on_event("startup")
def startup():
    global manager
    manager = MediaManager()
    loop = asyncio.get_event_loop()
    loop.create_task(manager.start_loop())


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/play")
async def play():
    await manager.play("MSEdge")


@app.get("/pause")
async def pause():
    await manager.pause("MSEdge")


@app.get("/thumb")
async def thumb():
    return await manager.get_media_item("MSEdge").get_thumbnail_base64_encoded()
