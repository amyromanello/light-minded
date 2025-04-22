from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import dataformat
import asyncio

app = FastAPI()
app.mount(
    "/webgl_output", StaticFiles(directory="web/webgl_output"), name="webgl_output"
)
event = asyncio.Event()
lock = asyncio.Lock()

gData: dataformat.ROIData


@app.get("/")
async def index():
    return FileResponse("web/brain_regions_3d.html")


@app.post("/set")
async def set(data: dataformat.ROIData):
    async with lock:
        global gData
        gData = data
        event.set()


@app.get("/get")
async def get():
    return gData


async def event_generator():
    await event.wait()
    async with lock:
        for i in gData.data:
            yield f"{i}"
    await event.clear()


@app.get("/events")
async def streamEvents():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
