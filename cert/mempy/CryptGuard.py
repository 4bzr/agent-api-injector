import psutil
import os, shutil, urllib.request, pyautogui, time, uvicorn, threading, logging, subprocess, ctypes
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from cert.utils.logger import debug, info, error, bridge, send_message, successinfo, warning, downloadCompiler
from cert.utils.utils import ClearLog
from ctypes import wintypes
from cert.certgg import CertAPI
from cert.utils.logger import printthread, printsinglethread, error

main_dir = os.path.dirname(os.path.abspath(__file__))
autoexec_path = os.path.join(main_dir, "autoexec")

global Cert
Cert = CertAPI()
Cert.SetAutoExecPath(autoexec_path)

class ThreadInfo:
    def __init__(self, threadId, isSuspended):
        self.threadId = threadId
        self.isSuspended = isSuspended

def get_process_id_by_name(processName):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == processName:
            return proc.info['pid']
    return None

def suspend_thread_by_id(processName, threads, threadIdToSuspend):
    processId = get_process_id_by_name(processName)
    if processId:
        for thread in threads:
            if thread.threadId == threadIdToSuspend:
                hThread = ctypes.windll.kernel32.OpenThread(0x0002, False, threadIdToSuspend)
                if hThread:
                    if ctypes.windll.kernel32.SuspendThread(hThread) != -1:
                        thread.isSuspended = True
                        printthread(f"Thread {threadIdToSuspend} suspended.")
                        ctypes.windll.kernel32.CloseHandle(hThread)
                        return True
                    else:
                        error(f"Failed to suspend thread: {ctypes.windll.kernel32.GetLastError()}")
                        ctypes.windll.kernel32.CloseHandle(hThread)
                        return False
        error("Thread not found or could not be suspended.")
        return False
    else:
        error("Process not found.")
        return False

def resume_thread_by_id(processName, threads, threadIdToResume):
    processId = get_process_id_by_name(processName)
    if processId:
        for thread in threads:
            if thread.threadId == threadIdToResume:
                hThread = ctypes.windll.kernel32.OpenThread(0x0002, False, threadIdToResume)
                if hThread:
                    if ctypes.windll.kernel32.ResumeThread(hThread) != -1:
                        thread.isSuspended = False
                        printthread(f"Thread {threadIdToResume} resumed.")
                        ctypes.windll.kernel32.CloseHandle(hThread)
                        return True
                    else:
                        error(f"Failed to resume thread: {ctypes.windll.kernel32.GetLastError()}")
                        ctypes.windll.kernel32.CloseHandle(hThread)
                        return False
        error("Thread not found or could not be resumed.")
        return False
    else:
        error("Process not found.")
        return False

def print_threads(threads):
    printthread("Threads:")
    for thread in threads:
        printthread(f"Thread ID: {thread.threadId}", "(Suspended)" if thread.isSuspended else "")

def CryptGuard():
    processName = "RobloxPlayerBeta.exe"
    processId = get_process_id_by_name(processName)
    if not processId:
        error("Process not found.")
        return

    threads = []
    for thread in psutil.Process(processId).threads():
        threads.append(ThreadInfo(thread.id, False))

    if threads == []:
        error("Couldnt find any Threads")
        return

    printthread("Available Threads:")
    for thread in threads:
        printthread(f"Thread ID: {thread.threadId}")

    printsinglethread(f"Suspending {len(threads)} ...")

    for i in range(min(5, len(threads))):
        suspend_thread_by_id(processName, threads, threads[i].threadId)

    print_threads(threads)

    printsinglethread(f"Resuming {len(threads)} ...")

    threading.Thread(target=LaunchCertMain, daemon=True).start()

    for i in range(min(5, len(threads))):
        time.sleep(1)
        resume_thread_by_id(processName, threads, threads[i].threadId)

    print_threads(threads)

    time.sleep(1)




Cert_ERRORCODES = {
    0x0: "Successfully injected!",
    0x1: "Currently injecting!",
    0x2: "Failed to find Roblox process.",
    0x3: "Failed to fetch DataModel :(",
    0x4: "Failed to fetch certain modules.",
    0x5: "Roblox terminated while injecting!",
    0x6: "Failed to find Bridge!"
}

async def execute(code):
    input_value = code
    try:
        if Cert.GetStatus() == 5:
            Cert.RunScript(input_value)
        else:
            pyautogui.alert("Not Injected")
    except Exception as e:
        error(f"Error executing code: {e}")

app = FastAPI()

logging.getLogger("uvicorn.error").propagate = False
logging.getLogger("uvicorn.access").propagate = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await execute(data)
    except WebSocketDisconnect:
        successinfo("The script has been executed.")
        

def start_websocket_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=8050, log_level="info")
    server = uvicorn.Server(config)
    successinfo("$: Server has been started.")
    successinfo("Welcome to  full!")    
    successinfo("Ready to use CF.")
    
    server.run()





def LaunchCertMain():
    launchstatus = Cert.Inject()

    if launchstatus == 0:
        send_message("Attached")
        print("")

        info("$: Starting webserver")
        threading.Thread(target=start_websocket_server, daemon=True).start()
    else:
        error_message = Cert_ERRORCODES.get(launchstatus, "Unknown error")
        send_message(error_message)
