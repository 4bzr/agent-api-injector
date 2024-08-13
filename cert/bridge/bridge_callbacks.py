from cert.utils.base import Window
from cert.utils.instance import Instance
from cert.bridge.bridge import Bridge as RBXBridge
from cert.utils.bytecode import Bytecode as RBXBytecode

import aiohttp, asyncio, ssl, threading, socket, struct
from aiohttp import web
from urllib.parse import urlparse

from cert.utils.logger import debug, info, error, bridge, startinfo, successinfo, send_message

import zlib
import ctypes
import psutil, shutil
import re, os, win32clipboard
import aiohttp, asyncio, subprocess
import marshal
import types

websocket_connections = {}
event_loop = None

user32 = ctypes.windll.user32
base_script = ["LocalScript", "ModuleScript"]

def path_no_escape(f_path: str):
    current_dir = os.getcwd()
    image_path = os.path.join(current_dir, "workspace", *f_path.split("\\"))

    return image_path.replace("..", "")

def get_formulated_filename(file_name: str) -> str:
    pass

async def send_websocket_message(url: str, message: str):
    print("Sending message...")
    ws = websocket_connections[url]
    await ws.send_str(message)
    print(f"Sent message to {url}: {message}")

def register_callbacks(Bridge: RBXBridge):
    global BridgeService
    BridgeService = Bridge

    #@BridgeService.RegisterCallback
    #def reset_module_bytecode(session: int, args: list[any]):
    #    if isinstance(args[0], Instance):
    #        args[0].ResetModule()

    #@BridgeService.RegisterCallback
    #def set_scriptable(session: int, args: list[any]):
    #    if (
    #        isinstance(args[0], Instance)
    #        and type(args[1]) == str
    #        and type(args[2]) == bool
    #    ):
    #        PropDescriptor = args[0].ClassDescriptor.PropertyDescriptors.Get(args[1])

    #        if PropDescriptor.Address < 1000:
    #            print(f"Bridge error: {args[1]} is not a valid property")
    #            return [False]

    #        PropDescriptor.SetScriptable(args[2])
    #        return [True]

    @BridgeService.RegisterCallback # TODO: FINISH THIS
    def get_rawmetatable(session:int, args: list[any]):
        # real 🤥
        pass

    # LOADSTRING FUNCTION
    @BridgeService.RegisterCallback
    def load_source(session: int, args: list[any]):
        if isinstance(args[0], Instance) and type(args[1]) == str:
            args[0].SetModuleBypass()
            args[0].Bytecode = RBXBytecode.Compile(
                f"return function(...) {args[1]} \nend", f"load-{session}.btc"
            )

            # TODO: return if compile success
            return [True]


    # INSTANCE
    @BridgeService.RegisterCallback
    def get_instance_address(session: int, args: list[any]):
        target_instance = args[0]

        if type(target_instance) == Instance:
            return [target_instance.Address]

    @BridgeService.RegisterCallback
    def spoof_instance(session: int, args: list[any]):
        spoofing = args[0]
        new_instance = args[1]

        if (
            type(spoofing) == Instance
            and (type(new_instance) == Instance
            or type(new_instance) == int)
        ):
            spoofing.Spoof(new_instance)

    @BridgeService.RegisterCallback
    def get_properties(session: int, args: list[any]):
        if isinstance(args[0], Instance):
            properties = []

            for Descriptor in args[0].ClassDescriptor.PropertyDescriptors.GetAllList():  # We filter in init script
                properties.append(Descriptor.Name)

            return [properties]
    

    # SCRIPTS
    @BridgeService.RegisterCallback
    def get_script_bytecode(session: int, args: list[any]):
        # TODO: implement bytecode decompressor
        # TODO: Add konstant or unluau
        succeed = False
        script_bytecode: bytes = None

        if isinstance(args[0], Instance) and args[0].ClassName in base_script:
            script_bytecode = args[0].Bytecode
            succeed = True if script_bytecode is bytes else False
        else:
            print("Bridge error: can't get bytecode because args[0] isn't a script")

        return [True, (script_bytecode.hex())]


    # HTTP LIBRARY
    @BridgeService.RegisterCallback
    def http_request(session: int, args: list[any]):
        options = args[0]
        if isinstance(options, dict):
            url = options.get("Url")

            if isinstance(url, str):
                def run_async(coro):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(coro)
                    loop.close()
                    return result

                async def _http_request(options):
                    url = options.get("Url")
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.request(
                                options.get("Method", "GET"),
                                url,
                                headers=options.get("Headers"),
                                cookies=options.get("Cookies"),
                                data=options.get("Body"),
                            ) as response:
                                response_data = {
                                    "Success": response.status == 200,
                                    "StatusCode": response.status,
                                    "StatusMessage": response.reason,
                                    "Headers": dict(response.headers),
                                    "Body": await response.text(errors="ignore"),
                                }
                                return [True, response_data]
                    except Exception as e:
                        print(f"Http Request Error: {e}")

                return run_async(_http_request(options))

    # MISC

    @BridgeService.RegisterCallback
    def websocket_connect(session: int, args: list[any]):
        # TODO Make this support multiple servers (basically this WebSocket.connect/this function can only be called once currently)

        url = args[0]

        if isinstance(url, str):
            # TODO: Check if WebSocket Server already exists on said host:port
            parsed_url = urlparse(url)

            def is_private_ip(ip):
                private_ranges = [
                    ("10.0.0.0", "10.255.255.255"),
                    ("172.16.0.0", "172.31.255.255"),
                    ("192.168.0.0", "192.168.255.255"),
                    ("127.0.0.0", "127.255.255.255"),
                ]

                ip = struct.unpack("!I", socket.inet_aton(ip))[0]
                for start, end in private_ranges:
                    if (
                        struct.unpack("!I", socket.inet_aton(start))[0]
                        <= ip
                        <= struct.unpack("!I", socket.inet_aton(end))[0]
                    ):
                        return True
                return False

            def is_internal(parsed_url):
                try:
                    hostname = parsed_url.hostname

                    if not hostname:
                        return False

                    # Check if hostname is an IP address
                    ip = socket.gethostbyname(hostname)
                    if is_private_ip(ip):
                        return True

                    return False
                except Exception as e:
                    print(f"Error determining if URL is internal: {e}")
                    return False

            queue = asyncio.Queue()

            async def websocket_handler(request):
                ws = web.WebSocketResponse()
                await ws.prepare(request)

                print("Client connected")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == "close":
                            # TODO Make this also close Server too
                            await ws.close()
                            BridgeService.Send(url + "_close")
                            print("Connection closed by client")
                        else:
                            await ws.send_str(msg.data)
                            BridgeService.Send(url + "_message", msg.data)
                            print("Received message:", msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"ws connection closed with exception {ws.exception()}")

                print("Client connection closed")

                return ws

            async def start_websocket_server():
                port = parsed_url.port

                if not port:
                    raise ValueError("Port number not specified in the URL")

                app = web.Application()
                app.add_routes([web.get("/", websocket_handler)])

                if parsed_url.scheme == "wss":
                    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE

                    runner = web.AppRunner(app, ssl_context=ssl_context)
                else:
                    runner = web.AppRunner(app)

                await runner.setup()

                site = web.TCPSite(runner, parsed_url.hostname, port)
                await site.start()
                info("The websocket server has started")
                await queue.put([True])

                await asyncio.Event().wait()  # Run forever

            def start_server_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_websocket_server(url))

            async def start_client_session():
                startinfo("Starting client session..")
                session = aiohttp.ClientSession()
                ws = await session.ws_connect(url)
                successinfo("Websocket started. Script execution can now be handled.")
                info("Do not close this window after injecting.")
                successinfo("The client session has started.")
                os.system('cls')
                successinfo("[agent] Done!")
                successinfo("POWERED BY THE CAS")
                websocket_connections[url] = ws

                await queue.put([True])

                await asyncio.Event().wait()  # Run forever

            def start_client_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_client_session())

            try:
                global event_loop
                # Create a new event loop for the server thread
                event_loop = asyncio.new_event_loop()

                result_server, result_client = None, None
                if is_internal(parsed_url):
                    server_thread = threading.Thread(
                        target=start_server_loop, args=[event_loop]
                    )
                    server_thread.start()

                    # Wait for the server to start
                    result_server = asyncio.run_coroutine_threadsafe(
                        queue.get(), event_loop
                    ).result()
                else:
                    result_server = True
                client_thread = threading.Thread(
                    target=start_client_loop, args=[event_loop]
                )
                client_thread.start()
                result_client = asyncio.run_coroutine_threadsafe(
                    queue.get(), event_loop
                ).result()

                return [result_server and result_client]
            except Exception as e:
                print(f"WebSocket Server Error {e}")
            # loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(loop)
            # loop.run_until_complete(main(url))
            # loop.run_forever()

    @BridgeService.RegisterCallback
    def websocket_send(session: int, args: list[any]):
        url, message = args[0], args[1]
        if isinstance(url, str) and isinstance(message, str):

            if url in websocket_connections:
                print("Connection found for URL")
                asyncio.run_coroutine_threadsafe(
                    send_websocket_message(url, message), event_loop
                ).result()
                return [True]
            else:
                print(f"No active WebSocket connection found for URL: {url}")

    @BridgeService.RegisterCallback
    def websocket_close(session: int, args: list[any]):
        url = args[0]
        if isinstance(url, str):
            if url in websocket_connections:
                print("Connection found for URL")
                asyncio.run_coroutine_threadsafe(
                    send_websocket_message(url, "close"), event_loop
                ).result()
                return [True]
            else:
                print(f"No active WebSocket connection found for URL: {url}")

    @BridgeService.RegisterCallback
    def get_custom_asset(session: int, args: list[any]):
        if isinstance(args[0], str):
            roblox_path_process = None

            file_path = path_no_escape(args[0])
            file_name = re.split(r"\\", args[0])[-1]

            for pid in psutil.pids():
                try:
                    if psutil.Process(pid).name() == "RobloxPlayerBeta.exe":
                        roblox_path_process = psutil.Process(pid).exe()
                        break
                except:
                    pass

            content_dir = os.path.join(os.path.dirname(roblox_path_process), "content", "catl_assets")
            os.makedirs(content_dir, exist_ok=True)

            dest_path = os.path.join(content_dir, file_name)
            if not os.path.exists(file_path):
                open(file_path, 'a').close()

            shutil.copy(file_path, dest_path)
            return [True, "rbxasset://" + file_name]
    
    @BridgeService.RegisterCallback
    def set_clipboard(session: int, args: list[any]):
        success = False

        if isinstance(args[0], str):
            win32clipboard.OpenClipboard()

            try:
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, args[0])
                success = True

            finally:
                win32clipboard.CloseClipboard()

        else:
            print("Bridge error: can't set to clipboard because args[0] isn't a string")

        return [success]

    @BridgeService.RegisterCallback
    def messagebox(session: int, args: list[any]):
        if (
            isinstance(args[0], str)
            and isinstance(args[1], str)
            and isinstance(args[2], int)
        ):
            result = user32.MessageBoxW(
                Window, args[0], args[1], args[2]
            )
            return [True, result]
        
    @BridgeService.RegisterCallback
    def get_hwid(session: int, args: list[any]):
        try:
            hwid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
            return [True, hwid]
        except Exception as e:
            print(f" BRIDGE ERROR: Failed to get HWID: {e}")
            return [False, None]


    # FILE SYSTEM LIBRARY
    @BridgeService.RegisterCallback
    def read_file(session: int, args: list[any]):
        f_path = path_no_escape(args[0])
        succeed, file_content = False, ""

        try:
            with open(f_path, "rb") as file:
                file_content = file.read().decode(encoding="ascii", errors="ignore")
                file.close()

            succeed = True
        except Exception as e:
            print(f"Bridge error: failed to read file '{f_path}'", e)

        return [succeed, file_content]

    @BridgeService.RegisterCallback
    def write_file(session: int, args: list[any]):
        f_path = path_no_escape(args[0])
        file_content = args[1]

        os.makedirs(os.path.dirname(f_path), exist_ok=True)

        try:
            with open(f_path, "wb") as file:
                file.write(file_content.encode(encoding="ascii", errors="ignore"))
            return [True]
        except Exception as e:
            print(f"Bridge error: failed to write file on '{f_path}'", e)
            return [False]

    @BridgeService.RegisterCallback
    def delete_dir(session: int, args: list[any]):
        f_path = path_no_escape(args[0])
        succeed = False

        try:
            if os.path.isfile(f_path):
                os.remove(f_path)

            elif os.path.isdir(f_path):
                shutil.rmtree(f_path)

            succeed = True
        except Exception as e:
            print(f"Bridge error: failed to delete path of '{f_path}'", e)

        return [succeed]

    @BridgeService.RegisterCallback
    def get_path_type(session: int, args: list[any]):
        f_path = path_no_escape(args[0])
        succeed, path_type = False, None

        try:
            if os.path.isfile(f_path):
                path_type = "file"

            elif os.path.isdir(f_path):
                path_type = "folder"

            succeed = True
        except Exception as e:
            print(f"Bridge error: failed to get path type of '{f_path}'", e)

        return [succeed, path_type]

    @BridgeService.RegisterCallback
    def list_files(session: int, args: list[any]):
        f_path = path_no_escape(args[0])
        succeed, paths = False, []

        if os.path.isdir(f_path):
            for root, dirs, files in os.walk(f_path):
                for name in files:
                    full_path = os.path.join(root, name)
                    paths.append(full_path.split("workspace\\")[-1])
                for name in dirs:
                    full_path = os.path.join(root, name)
                    paths.append(full_path.split("workspace\\")[-1])

            succeed = True

        return [succeed, (paths if succeed else None)]

    @BridgeService.RegisterCallback
    def make_folder(session: int, args: list[any]):
        f_path = path_no_escape(args[0])
        succeed = False

        try:
            if not os.path.isdir(f_path):
                os.mkdir(f_path)

            succeed = True
        except Exception as e:
            print(f"Bridge error: failed to make folder in '{f_path}'", e)

        return [succeed]
