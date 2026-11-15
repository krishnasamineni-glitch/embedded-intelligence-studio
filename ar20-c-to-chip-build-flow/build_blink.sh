#!/bin/sh
# build_blink.sh - the whole path from C to a hex file, with the free LLVM tools (clang, ld.lld, llvm-objcopy).
# Keil does the same steps with armclang, armlink and fromelf.
set -e
for f in startup blink_main; do
  clang --target=thumbv7m-none-eabi -mcpu=cortex-m3 -mthumb -Os -ffreestanding -fno-common \
        -fno-unwind-tables -fno-asynchronous-unwind-tables -c $f.c -o $f.o      # compiler: C -> object file
done
ld.lld -T lpc1768.ld -Map=blink.map startup.o blink_main.o -o blink.elf          # linker: objects -> executable
llvm-size blink.elf                                                              # text 282, data 4, bss 4
llvm-objcopy -O binary blink.elf blink.bin                                       # raw bytes from address 0
python3 lpc_checksum.py blink.bin                                                # word 7 = 0xEFFF7CB8
llvm-objcopy -I binary -O ihex blink.bin blink.hex                               # Intel hex for the flash tools
head -2 blink.hex
