import importlib
import subprocess
import sys
import os

required_packages = [
    "aiohttp",
    "flask",
    "flask_cors",
]

def install_package(pkg):
    
    try:
        print(f"📦 Installing missing package: {pkg} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
    except Exception as e:
        print(f"❌ Failed to install {pkg}: {e}")

def ensure_dependencies():
    
    for pkg in required_packages:
        try:
            importlib.import_module(pkg.replace("-", "_"))
        except ImportError:
            install_package(pkg)

ensure_dependencies()
import asyncio
import aiohttp
import threading
import uuid
import json
import time
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from typing import Dict
from pathlib import Path
from flask_cors import CORS
# ---------- Config ----------
OUTPUT_DIR = Path("./downloads")
OUTPUT_DIR.mkdir(exist_ok=True)
# At the top, after OUTPUT_DIR.mkdir(exist_ok=True)
existing_files = list(OUTPUT_DIR.glob("*"))
existing_numbers = []
clients = []
for f in existing_files:
    stem = f.stem
    if stem.isdigit():
        existing_numbers.append(int(stem))

file_counter = max(existing_numbers, default=0) 


DEFAULT_SETTINGS = {
    "download_folder": "./downloads",
    "max_concurrent": 2,
    "max_retries": 10,
    "download_timeout": 60,
    "chunk_size": 64,
    "auto_dark_mode": False
}


CURRENT_SETTINGS = DEFAULT_SETTINGS.copy()
SETTINGS_FILE = "settings.json"


if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, 'r') as f:
            loaded_settings = json.load(f)
            CURRENT_SETTINGS.update(loaded_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")


MAX_CONCURRENT = CURRENT_SETTINGS["max_concurrent"]
CHUNK_SIZE = 1024 * CURRENT_SETTINGS["chunk_size"]
HEAD_TIMEOUT = 15
GET_TIMEOUT = CURRENT_SETTINGS["download_timeout"]
OUTPUT_DIR = Path(CURRENT_SETTINGS["download_folder"])
OUTPUT_DIR.mkdir(exist_ok=True)
# ----------------------------

app = Flask(__name__)
CORS(app)

tasks: Dict[str, dict] = {}
tasks_lock = threading.Lock()

file_counter_lock = threading.Lock()
loop = asyncio.new_event_loop()

def ensure_semaphore():
    if not hasattr(loop, "_semaphore"):
        loop._semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def download_worker(semaphore: asyncio.Semaphore, url: str, task_id: str):
    async with semaphore:
        max_retries = CURRENT_SETTINGS["max_retries"]
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if retry_count == 0:
                    tasks[task_id]["status"] = "starting"
                else:
                    tasks[task_id]["status"] = f"retrying ({retry_count}/{max_retries})"
                
                timeout = aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=CURRENT_SETTINGS["download_timeout"])
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    size = None
                    try:
                        head = await session.head(url, timeout=HEAD_TIMEOUT, allow_redirects=True)
                        if head.status < 400 and head.headers.get("Content-Length"):
                            size = int(head.headers.get("Content-Length"))
                    except Exception:
                        size = None

                    tasks[task_id]["total_bytes"] = size or 0
                    tasks[task_id]["status"] = "downloading"

                    
                    filename = None
                    downloaded = 0
                    resume_mode = False
                    
                    if retry_count > 0 and tasks[task_id].get("filename"):
                        filename = Path(tasks[task_id]["filename"])
                        if filename.exists():
                            downloaded = filename.stat().st_size
                            resume_mode = True
                    
                    if not filename:
                        global file_counter
                        with file_counter_lock:
                            file_counter += 1
                            n = file_counter
                        ext = ".mp4" if ".mp4" in url.lower() else (Path(url).suffix or ".mp4")
                        filename = OUTPUT_DIR / f"{n}{ext}"
                        tasks[task_id]["filename"] = str(filename)

                    headers = {}
                    if resume_mode and downloaded > 0:
                        headers["Range"] = f"bytes={downloaded}-"

                    async with session.get(url, timeout=CURRENT_SETTINGS["download_timeout"], headers=headers) as resp:
                        if resume_mode and resp.status == 206: 
                            mode = "ab"
                        elif resp.status == 200:
                            mode = "wb"  
                            downloaded = 0 
                        else:
                            resp.raise_for_status()

                        with open(filename, mode) as f:
                            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                                if not chunk:
                                    continue
                                f.write(chunk)
                                downloaded += len(chunk)
                                tasks[task_id]["downloaded_bytes"] = downloaded
                                if tasks[task_id].get("total_bytes"):
                                    try:
                                        tasks[task_id]["progress"] = round(downloaded / tasks[task_id]["total_bytes"] * 100, 2)
                                    except Exception:
                                        tasks[task_id]["progress"] = None
                                else:
                                    tasks[task_id]["progress"] = None
                        
                        tasks[task_id]["status"] = "completed"
                        tasks[task_id]["progress"] = 100.0
                        tasks[task_id]["retry_count"] = retry_count
                        return 
                        
            except Exception as e:
                retry_count += 1
                tasks[task_id]["retry_count"] = retry_count
                
                if retry_count <= max_retries:
                    tasks[task_id]["status"] = f"retrying ({retry_count}/{max_retries})"
                    tasks[task_id]["error"] = f"Attempt {retry_count} failed: {str(e)}"
                   
                    await asyncio.sleep(min(2 ** retry_count, 30)) 
                else:
                    
                    tasks[task_id]["status"] = "error"
                    tasks[task_id]["error"] = f"Failed after {max_retries} retries: {str(e)}"
                    
                   
                    if tasks[task_id].get("filename"):
                        try:
                            file_path = Path(tasks[task_id]["filename"])
                            if file_path.exists():
                                file_path.unlink()
                                tasks[task_id]["filename"] = None
                        except Exception as cleanup_error:
                            tasks[task_id]["error"] += f" (Cleanup failed: {cleanup_error})"
                    break

async def enqueue_download(url: str):
    task_id = str(uuid.uuid4())
    with tasks_lock:
        tasks[task_id] = {
            "id": task_id,
            "url": url,
            "status": "queued",
            "progress": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "filename": None,
            "error": None,
            "retry_count": 0,
        }
    ensure_semaphore()
    coro = download_worker(loop._semaphore, url, task_id)
    asyncio.run_coroutine_threadsafe(coro, loop)
    return task_id

def start_loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop_in_thread, args=(loop,), daemon=True).start()

# ---------- Flask routes ----------



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/enqueue", methods=["POST"])
def enqueue():
    data = request.get_json(force=True)
    url = data.get("url")
    if not url:
        return jsonify({"error":"no url provided"}),400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error":"url must start with http:// or https://"}),400
    fut = asyncio.run_coroutine_threadsafe(enqueue_download(url), loop)
    task_id = fut.result()
    return jsonify({"ok": True, "id": task_id})

@app.route("/bulk_enqueue", methods=["POST"])
def bulk_enqueue():
    data = request.get_json(force=True)
    urls = data.get("urls", [])
    
    if not urls:
        return jsonify({"error": "no urls provided"}), 400
    
    if not isinstance(urls, list):
        return jsonify({"error": "urls must be a list"}), 400
    
    valid_urls = []
    task_ids = []
    
    for url in urls:
        if not isinstance(url, str):
            continue
        url = url.strip()
        if url and (url.startswith("http://") or url.startswith("https://")):
            valid_urls.append(url)
            fut = asyncio.run_coroutine_threadsafe(enqueue_download(url), loop)
            task_id = fut.result()
            task_ids.append(task_id)
    
    if not valid_urls:
        return jsonify({"error": "no valid urls found"}), 400
    
    return jsonify({"ok": True, "count": len(valid_urls), "task_ids": task_ids})
@app.route("/status")
def status():
    def event_stream():
        
        last_snapshot = {}
        while True:
            with tasks_lock:
                snapshot = {tid: dict(info) for tid, info in tasks.items()}
            if snapshot != last_snapshot:
                yield f"data: {json.dumps(snapshot)}\n\n"
                last_snapshot = snapshot
            time.sleep(0.5) 
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current settings"""
    return jsonify(CURRENT_SETTINGS)

@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Update settings"""
    global CURRENT_SETTINGS, MAX_CONCURRENT, CHUNK_SIZE, GET_TIMEOUT, OUTPUT_DIR
    
    try:
        data = request.get_json()
        
      
        if "download_folder" in data:
            if not isinstance(data["download_folder"], str) or not data["download_folder"].strip():
                return jsonify({"success": False, "error": "Invalid download folder"}), 400
        
        if "max_concurrent" in data:
            if not isinstance(data["max_concurrent"], int) or data["max_concurrent"] < 1 or data["max_concurrent"] > 10:
                return jsonify({"success": False, "error": "Max concurrent must be between 1 and 10"}), 400
        
        if "max_retries" in data:
            if not isinstance(data["max_retries"], int) or data["max_retries"] < 1 or data["max_retries"] > 20:
                return jsonify({"success": False, "error": "Max retries must be between 1 and 20"}), 400
        
        if "download_timeout" in data:
            if not isinstance(data["download_timeout"], int) or data["download_timeout"] < 30 or data["download_timeout"] > 300:
                return jsonify({"success": False, "error": "Download timeout must be between 30 and 300 seconds"}), 400
        
        if "chunk_size" in data:
            if not isinstance(data["chunk_size"], int) or data["chunk_size"] < 16 or data["chunk_size"] > 1024:
                return jsonify({"success": False, "error": "Chunk size must be between 16 and 1024 KB"}), 400
        
        if "auto_dark_mode" in data:
            if not isinstance(data["auto_dark_mode"], bool):
                return jsonify({"success": False, "error": "Auto dark mode must be boolean"}), 400
        
        # Update settings
        CURRENT_SETTINGS.update(data)
        
        # Apply settings to global variables
        MAX_CONCURRENT = CURRENT_SETTINGS["max_concurrent"]
        CHUNK_SIZE = 1024 * CURRENT_SETTINGS["chunk_size"]
        GET_TIMEOUT = CURRENT_SETTINGS["download_timeout"]
        
        # Update output directory
        new_output_dir = Path(CURRENT_SETTINGS["download_folder"])
        if new_output_dir != OUTPUT_DIR:
            OUTPUT_DIR = new_output_dir
            OUTPUT_DIR.mkdir(exist_ok=True)
        print(f"Output directory updated to: {OUTPUT_DIR}")
        print(f"Settings updated: {CURRENT_SETTINGS}")
        print(f"Max concurrent: {MAX_CONCURRENT}")
        print(f"Chunk size: {CHUNK_SIZE}")
        print(f"Download timeout: {GET_TIMEOUT}")
        print(f"Output directory: {OUTPUT_DIR}")
        print(f"Auto dark mode: {CURRENT_SETTINGS['auto_dark_mode']}")
        print(f"Max retries: {CURRENT_SETTINGS['max_retries']}")
        print(f"Download folder: {CURRENT_SETTINGS['download_folder']}")
        print(f"Max concurrent: {MAX_CONCURRENT}")
       
        if hasattr(loop, "_semaphore"):
            loop._semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
       
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(CURRENT_SETTINGS, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            return jsonify({"success": False, "error": f"Failed to save settings: {e}"}), 500
        
        return jsonify({"success": True, "message": "Settings updated successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid request: {e}"}), 400

@app.route("/api/getsize", methods=["POST"])
def getsize():
    data = request.get_json(force=True)
    fpath = data.get("dirpath")
    print(fpath)
    totsize = 0
    for dirpath, dirname, filenames in os.walk(fpath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            totsize += os.path.getsize(fp)
    totsize = totsize /(1024*1024)
    return jsonify({"size": totsize}), 200

@app.route("/api/settings/reset", methods=["POST"])
def reset_settings():
    """Reset settings to defaults"""
    global CURRENT_SETTINGS, MAX_CONCURRENT, CHUNK_SIZE, GET_TIMEOUT, OUTPUT_DIR
    
    try:
        CURRENT_SETTINGS = DEFAULT_SETTINGS.copy()
        
    
        MAX_CONCURRENT = CURRENT_SETTINGS["max_concurrent"]
        CHUNK_SIZE = 1024 * CURRENT_SETTINGS["chunk_size"]
        GET_TIMEOUT = CURRENT_SETTINGS["download_timeout"]
        OUTPUT_DIR = Path(CURRENT_SETTINGS["download_folder"])
        OUTPUT_DIR.mkdir(exist_ok=True)
        
       
        if hasattr(loop, "_semaphore"):
            loop._semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
       
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(CURRENT_SETTINGS, f, indent=2)
        
        return jsonify({"success": True, "message": "Settings reset to defaults"})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to reset settings: {e}"}), 500
@app.route("/api/cleanup_done", methods=["POST"])
def cleanup_done_tasks():
    """Remove tasks with status 'completed' from memory"""
    with tasks_lock:
        done_keys = [tid for tid, info in tasks.items() if info.get("status") == "completed"]
        for tid in done_keys:
            tasks.pop(tid, None)
    return jsonify({
        "success": True,
        "removed_count": len(done_keys),
        "message": f"Removed {len(done_keys)} completed task(s)"
    })


if __name__=="__main__":
    
    os.system('cls' if os.name == 'nt' else 'clear')

    print("✅ All dependencies are installed and ready!")
    print("Starting Flask server on port ", PORT)
    url = f"http://127.0.0.1:{PORT}"

 
    if os.name == "nt": 
        os.system(f'start {url}')
    else:  
        os.system(f'xdg-open {url} >/dev/null 2>&1 &')

    app.run(debug=True, threaded=True , port=PORT)

