# lpc_checksum.py <image.bin> - writes the LPC17xx checksum into word 7 (the sum of words 0..7 must be 0),
# the same thing Keil and Flash Magic do automatically. Prints the value.
import struct
import sys

path = sys.argv[1]
b = bytearray(open(path, 'rb').read())
words = struct.unpack('<7I', b[:28])
ck = (-sum(words)) & 0xFFFFFFFF
b[28:32] = struct.pack('<I', ck)
open(path, 'wb').write(b)
print(f'word 7 = 0x{ck:08X}  (sum of words 0..7 = 0x{sum(struct.unpack("<8I", b[:32])) & 0xFFFFFFFF:08X})')
