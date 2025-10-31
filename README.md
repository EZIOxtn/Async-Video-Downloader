# Async (FB/IG) Video Downloader

### Download Instagram & Facebook videos asynchronously with Python and Flask



![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![AsyncIO](https://img.shields.io/badge/Async-Enabled-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Flask](https://img.shields.io/badge/Flask-API-orange)


## 🚀 Overview
**Async Video Downloader** is a lightweight, high-performance tool for downloading videos from **Instagram** and **Facebook**.  
It combines a **console-based async engine** (using `aiohttp` and `asyncio`) with a **Flask-based web interface** for managing downloads easily through your browser.

This project is built to handle **multiple downloads concurrently**, retry failed tasks, and track progress in real time — all while using minimal system resources.

---

## 🧩 Features
✅ **Fast & Non-blocking:** Fully asynchronous download engine  
✅ **Web Dashboard:** Flask server to manage and view tasks  
✅ **Cross-Platform:** Works on Linux, Windows, and macOS  
✅ **Concurrent Downloads:** Configure max downloads and retry limits  
✅ **Auto Dependency Installation:** Missing packages are automatically installed  


---
## 🖥️ Architecture
---
[ Flask Web Server ] <--> [ Async Downloader Core ]
↑ ↓
Browser UI aiohttp + asyncio

- **Flask** handles the frontend UI and API endpoints.  
- **aiohttp** manages async HTTP sessions for downloading.  
- **Threading + asyncio loop** ensures responsiveness and high throughput.

---


## ⚙️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/async-video-downloader.git
cd async-video-downloader
```
### 2️⃣ Run the script
The script auto-installs dependencies if they’re missing:
```bash
python3 app.py #or py app.py
```
###3️⃣ Open the dashboard
Once started, open your browser at:

```
http://127.0.0.1:5000
```

## 🧠 Usage

🔹 Web Mode
### run facebook videos in mobile perspective (dimensions):
copy and paste the content of the fb_video_script.js file and paste it in the dev  console
keep scrolling a little , the type 
```
stop();
```
 in the console
### after starting the flask server :

Drag and drop a .txt file containing URLs (one per line).

Monitor progress, retry failed downloads, and clean completed tasks.

Use the Settings Dashboard to adjust:

Download folder

Maximum concurrent downloads 

Retry limits


## 🧰 API Endpoints

| Method | Endpoint | Description |



| `POST` | `/api/bulk_enqueue` | Add URLs to download queue |

| `GET`  | `/api/status` | List all tasks with status |

| `POST` | `/api/cleanup_done` | Remove completed downloads |

| `GET`  | `/api/getsize` | Get the size of the download folder |

## 🕹️ Example
```python
import requests

response = requests.post("http://127.0.0.1:5000/api/enqueue", json={
    "urls": [
        "https://scontent.fnbe1-2.fna.fbcdn.net/o1/v/t2/f2/m412/..." #ListOfUrls
        
    ]
})

print(response.json())

```
## 💡 Notes

- This project is designed to run on a **local server** for **personal and educational use only**.  
- It is **not intended for public hosting** or production deployment.  
- Please ensure you comply with each platform’s **Terms of Service** before downloading or using any content.

---

## 🧑‍💻 Tech Stack

- **Python 3.9+**
- **Flask** + **Flask-CORS**
- **aiohttp** + **asyncio**
- **threading**, **uuid**, **json**, **pathlib**

---

## 🏁 License

This project is released under the **MIT License**.  
You are free to modify, distribute, and use it — with proper **attribution**.

---

## ⭐ Credits

Developed with ❤️ using **Flask** and **AsyncIO**.  
If you find this project helpful, please consider giving it a ⭐ on GitHub!

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.


## screenshot's 
<img width="1890" height="895" alt="image" src="https://github.com/user-attachments/assets/dae5c7ca-fe38-437b-900b-9b8328bbb0a0" />




## License

