
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess, json, os

app = FastAPI(title="Unified Bots Platform")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return open("templates/index.html",encoding="utf8").read()

@app.post("/run-ai")
async def run_ai(text: str = Form(...)):
    # placeholder call – you can integrate AI.py logic here
    return {"reply":"AI response: "+text}

@app.post("/text-correction")
async def correction(text: str = Form(...)):
    return {"result": text.strip().capitalize()}

@app.post("/file-analysis")
async def file_analysis(file: UploadFile = File(...)):
    data = await file.read()
    return {"size": len(data)}

@app.post("/html-preview")
async def html_preview(code: str = Form(...)):
    return {"preview": code[:500]}

@app.get("/bots-list")
def list_bots():
    return {"bots": os.listdir("bots")}
