import ctypes, win32con
import win32api
import win32con
import win32process

windll = ctypes.windll

kernel32 = windll.kernel32
ntdll = windll.ntdll

ALLOWED_PROTECTIONS = [
    0x02, # PAGE_READONLY
    0x04, # PAGE_READWRITE
    0x20, # PAGE_EXECUTE_READONLY
    0x40 # PAGE_EXECUTE_READWRITE
]

PROTECTIONS = {
    "READ_ONLY": 0x02,
    "READ_WRITE": 0x04,
    "EXEC_READ_ONLY": 0x20,
    "EXEC_READ_WRITE": 0x40,
}

class MEMORY_BASIC_INFORMATION32(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_ulong),
        ("AllocationBase", ctypes.c_ulong),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_ulong),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong)
    ]

class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_ulonglong),
        ("AllocationBase", ctypes.c_ulonglong),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_ulonglong),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]

ptr_size = ctypes.sizeof(ctypes.c_void_p)
if ptr_size == 8:
    MEMORY_BASIC_INFORMATION = MEMORY_BASIC_INFORMATION64
elif ptr_size == 4:
    MEMORY_BASIC_INFORMATION = MEMORY_BASIC_INFORMATION32

kernel32.VirtualQueryEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION),
    ctypes.c_ulong
]

kernel32.VirtualQueryEx.restype = ctypes.c_ulong
kernel32.VirtualAllocEx.restype = ctypes.c_void_p

class Memopy:
    ctypes = ctypes
    process_handle = -1

    def __init__(self, process: int):
        self.process_handle = kernel32.OpenProcess(0x1F0FFF, False, process)

    def update_pid(self, pid: int):
        self.process_handle = kernel32.OpenProcess(0x1F0FFF, False, pid)

    def virtual_query(self, address):
        class MEMORY_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", ctypes.c_ulong),
                ("RegionSize", ctypes.c_size_t),
                ("State", ctypes.c_ulong),
                ("Protect", ctypes.c_ulong),
                ("Type", ctypes.c_ulong),
            ]

        memory_basic_info = MEMORY_BASIC_INFORMATION()
        
        # if this gets patched go use kernel32
        status = ntdll.NtQueryVirtualMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            0,  # MemoryBasicInformation
            ctypes.byref(memory_basic_info),
            ctypes.sizeof(memory_basic_info),
            None
        )
        
        if status != 0:
            raise ctypes.WinError()


    def suspend(self):
        ntdll.NtSuspendProcess(self.process_handle)

    def resume(self):
        ntdll.NtResumeProcess(self.process_handle)

    def pattern_scan(self, pattern: bytes, single=True):
        pattern_len = len(pattern)
        region = 0
        found = [] if not single else None

        while region < 0x7FFFFFFF0000:
            mbi = self.virtual_query(region)

            if mbi.State != 0x1000 or mbi.Protect not in (win32con.PAGE_READWRITE, win32con.PAGE_EXECUTE_READWRITE):
                region += mbi.RegionSize
                continue

            current_bytes = self.read_memory(region, mbi.RegionSize)
            for i in range(mbi.RegionSize - pattern_len + 1):
                if current_bytes[i:i + pattern_len] == pattern:
                    found_address = region + i
                    if single:
                        return found_address
                    else:
                        found.append(found_address)

            region += mbi.RegionSize

        return found

    # memory functions

    def virtual_protect(self, address: int, size: int, protect_val: int):
        old_prot_val = ctypes.c_ulong()
        result = ctypes.windll.kernel32.VirtualProtectEx(
            self.process_handle,
            ctypes.c_void_p(address),
            size,
            protect_val,
            ctypes.byref(old_prot_val)
        )
        if not result:
            raise ctypes.WinError()
        return old_prot_val.value

    def unlock_memory(self, address: int, size: int):
        return ntdll.NtUnlockVirtualMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            size,
            0x01
        )

    def allocate_memory(self, size: int, address: int = None) -> int: # if this gets patched use kernel32 to allocate
        addr = ctypes.c_void_p(address) if address else None
        base_address = ctypes.c_void_p()
        
        status = ntdll.NtAllocateVirtualMemory(
            self.process_handle,
            ctypes.byref(base_address),
            0,
            ctypes.byref(ctypes.c_size_t(size)),
            win32con.MEM_RESERVE | win32con.MEM_COMMIT,
            win32con.PAGE_READWRITE
        )

        if status != 0:
            raise ctypes.WinError()

        return base_address.value


    def free_memory(self, address: int, size: int): # if this gets patched then use kernel32 to freememory
        return ntdll.NtFreeVirtualMemory(
            self.process_handle,
            ctypes.byref(ctypes.c_void_p(address)),
            ctypes.byref(ctypes.c_size_t(size)),
            0x8000
        )

    def read_memory(self, buffer, address: int):
        size = ctypes.sizeof(buffer)
        ntdll.NtReadVirtualMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            size,
            None
        )
        self.unlock_memory(address, size)
        
        
    def write_memory(self, buffer, address: int) -> None:
        size = ctypes.sizeof(buffer)
        old_prot = self.virtual_protect(address, size, PROTECTIONS["READ_WRITE"])
        
        # if this gets patched go use kernel32 to write
        status = ntdll.NtWriteVirtualMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            ctypes.pointer(buffer),
            size,
            None
        )
        
        if status != 0:
            raise ctypes.WinError()

        self.virtual_protect(address, size, old_prot)



    # read functions

    def read_byte(self, address: int, buffer_size: int = 1) -> bytes:
        buffer = ctypes.create_string_buffer(buffer_size)
        self.read_memory(buffer, address)

        return buffer.raw

    def read_bytes(self, address: int, length=4096) -> bytes:
        buffer = (length * ctypes.c_char)()
        self.read_memory(buffer, address)

        return buffer.raw

    def read_string(self, address: int, length: int = 100) -> str:
        data = self.read_byte(address, length)
        null_index = data.find(b'\x00')
        if null_index != -1:
            data = data[:null_index]
        return data.decode(errors="ignore")

    def read_double(self, address: int) -> float:
        buffer = ctypes.c_double()
        self.read_memory(buffer, address)

        return buffer.value

    def read_float(self, address: int) -> float:
        buffer = ctypes.c_float()
        self.read_memory(buffer, address)

        return buffer.value

    def read_long(self, address: int) -> int:
        buffer = ctypes.c_long()
        self.read_memory(buffer, address)

        return buffer.value

    def read_longlong(self, address: int) -> int:
        buffer = ctypes.c_longlong()
        self.read_memory(buffer, address)

        return buffer.value

    # write functions

    def write_value(self, address: int, value, data_type):
        buffer = data_type(value)
        self.write_memory(buffer, address)

    def write_byte(self, address: int, value: int):
        self.write_value(address, value, ctypes.c_char)

    def write_bytes(self, address: int, value: bytes):
        buffer = (ctypes.c_char * len(value)).from_buffer_copy(value)
        self.write_memory(buffer, address)

    def write_string(self, address: int, value: str):
        encoded_value = value.encode(errors="ignore") + b"\x00"
        self.write_bytes(address, encoded_value)

    def write_double(self, address: int, value: float):
        self.write_value(address, value, ctypes.c_double)

    def write_float(self, address: int, value: float):
        self.write_value(address, value, ctypes.c_float)

    def write_long(self, address: int, value: int):
        self.write_value(address, value, ctypes.c_long)

    def write_longlong(self, address: int, value: int):
        self.write_value(address, value, ctypes.c_longlong)