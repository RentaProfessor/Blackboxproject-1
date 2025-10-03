"""
BLACK BOX UI - Simple Web Server
Serves static UI files
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

# Serve static files
@app.get("/")
async def root():
    return FileResponse("/app/index.html")

@app.get("/styles.css")
async def styles():
    return FileResponse("/app/styles.css")

@app.get("/app.js")
async def appjs():
    return FileResponse("/app/app.js")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")

