import colorama, websocket, time, os, ctypes, shutil, urllib.request
from colorama import Fore, Style
colorama.init(autoreset=True)

debugmode = True
threaddebugmode = False
debugmode2 = True

def debug(*args, **kwargs):
    if debugmode == True:
        print(Fore.YELLOW + "dbg:", *args, **kwargs)

def bridge(*args, **kwargs):
    if debugmode == True:
        print("")
        print(Fore.GREEN + "agent:", *args, **kwargs)

def info(*args, **kwargs):
    if debugmode == True:
        print(Fore.BLUE + "inf:", *args, **kwargs)

def error(*args, **kwargs):
    if debugmode == True:
        print(Fore.RED + "err:", *args, **kwargs)

def offset(*args, **kwargs):
    if debugmode == True:
        print(Fore.GREEN + "off:", *args, **kwargs)

def updatetag(*args, **kwargs):
    if debugmode == True:
        print(Fore.LIGHTBLUE_EX + "upd:", *args, **kwargs)

def printthread(*args, **kwargs):
    if threaddebugmode == True:
        print(Fore.GREEN + "thr:", *args, **kwargs)

def warning(*args, **kwargs):
    if debugmode == True:
        print(Fore.YELLOW + "war:", *args, **kwargs)

def startinfo(*args, **kwargs):
    if debugmode == True:
        print(Fore.RED + "str:", *args, **kwargs)

def successinfo(*args, **kwargs):
    if debugmode == True:
        print(Fore.LIGHTGREEN_EX + "suc:", *args, **kwargs)

def printsinglethread(*args, **kwargs):
    if debugmode == True and threaddebugmode == False:
        print("")
        print(Fore.MAGENTA + "thr:", *args, **kwargs)
        print("")

def send_message(message):
    if debugmode2 == False:
        try:
            ws = websocket.create_connection("ws://localhost:8060/ws/")
            ws.send(message)
            ws.close()
        except Exception as e:
            error("IMPORTANT ERROR WHILE SENDING MESSAGE:", e)
            time.sleep(1)
            send_message(message)

def downloadCompiler():
    def set_hidden_attribute(file_path):
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_HIDDEN)

    def download_file(url, file_name, target_dir):
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            set_hidden_attribute(target_dir)
        else:
            shutil.rmtree(target_dir)
            os.makedirs(target_dir)
            set_hidden_attribute(target_dir)
        
        target_file_path = os.path.join(target_dir, file_name)
        urllib.request.urlretrieve(url, target_file_path)

    if debugmode2 == False:
        startinfo("DLL file is downloading...")
        download_file('https://github.com/bv709sites/killniggers/releases/download/V30API/API.dll', 'API.dll', 'bin')
        startinfo("Finished downloading the dll.")
        startinfo("DLL is already added to path.")