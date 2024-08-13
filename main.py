
import requests
import zipfile
from io import BytesIO

import ctypes, os, shutil, urllib.request, pyautogui, time, uvicorn, threading, logging, subprocess
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from cert.utils.logger import debug, info, error, bridge, send_message, updatetag, startinfo, successinfo, downloadCompiler
from cert.utils.utils import ClearLog
from cert.mempy.CryptGuard import CryptGuard
import binascii  # hex encoding
import hashlib
import json as jsond  # json
import os
import platform  # check platform
import subprocess  # needed for mac device
import sys
import time  # sleep before exit
from datetime import datetime
from time import sleep
from uuid import uuid4  # gen random guid
import hmac

# GitHub repository details for update checking
GITHUB_REPO = "bv709sites/iwannakillmyself"
GITHUB_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
LOCAL_VERSION_FILE = "version.txt"
TEMP_DIR = "temp_update"

def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_latest_version():
    response = requests.get(GITHUB_URL)
    data = response.json()
    return data["tag_name"], data["zipball_url"]

def download_and_extract(url, extract_to="."):
    response = requests.get(url)
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        z.extractall(extract_to)

def update_application():
    latest_version, download_url = get_latest_version()
    local_version = get_local_version()

    if local_version == latest_version:
        info("You already have the latest version.")
        return

    updatetag(f"Updating from version {local_version} to {latest_version}...")
    
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    download_and_extract(download_url, TEMP_DIR)

    for item in os.listdir(TEMP_DIR):
        s = os.path.join(TEMP_DIR, item)
        d = os.path.join(".", item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.move(s, d)
        else:
            shutil.move(s, d)

    shutil.rmtree(TEMP_DIR)

    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(latest_version)

    successinfo("Update complete. Restarting application...")

    os.execl(sys.executable, sys.executable, *sys.argv)

# Run update check at the beginning
if __name__ == "__main__":
    update_application()
    

# Continue with the rest of your script after update check
downloadCompiler()

from cert.certgg import CertAPI

if __name__ == "__main__":
    CryptGuard()
    while True:
        time.sleep(1)
