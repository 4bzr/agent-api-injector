
import os, ctypes
import xxhash
import zstandard as zstd

dll = ctypes.CDLL("././bin/API.dll")

RBXCompile_t = dll.RBXCompile
RBXCompile_t.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

RBXDecompress_t = dll.RBXDecompress
RBXDecompress_t.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

class Bytecode:
    def Compile(source: str, path="compressed.btc"):
        RBXCompile_t(
            path.encode(errors="ignore"), 
            source.encode(errors="ignore")
        )

        try:
            with open(path, "rb") as file:
                file = open(path, "rb")
                bytecode = file.read().split(b" size: ")
                file.close()

        except:
            pass

        os.remove(path)

        return [bytecode[0], int(bytecode[1])]

    def Decompress(source):
        kBytecodeMagic = b'RSB1'
        kBytecodeHashMultiplier = 41
        kBytecodeHashSeed = 42
        try:
            ss = bytearray(source)
            
            hb = ss[:4]
            
            for i in range(4):
                hb[i] ^= kBytecodeMagic[i]
                hb[i] = (hb[i] - i * kBytecodeHashMultiplier) % 256

            for i in range(len(ss)):
                ss[i] ^= (hb[i % 4] + i * kBytecodeHashMultiplier) % 256

            hash_bytes = hb[:4]
            hash_value = int.from_bytes(hash_bytes, 'little')
            rehash = xxhash.xxh32(ss, seed=kBytecodeHashSeed).intdigest()

            if rehash != hash_value:
                return b"Failed to decompress bytecode. (1)"

            decompressed_size = int.from_bytes(ss[4:8], 'little')
            compressed_data = ss[8:]
            
            dctx = zstd.ZstdDecompressor()
            decompressed = dctx.decompress(compressed_data, max_output_size=decompressed_size)
            return decompressed
        except:
            return b"Failed to decompress bytecode. (2)"