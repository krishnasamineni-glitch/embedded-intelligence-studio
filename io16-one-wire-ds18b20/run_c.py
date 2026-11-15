# run_c.py - compile a small C file for the Cortex-M3 (clang), link it, and call its functions on an emulated
# M-class core with the LPC1768 memory map, logging every peripheral write. Used to check the video examples.
import os
import struct
import subprocess
import tempfile

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3

LD = """MEMORY { FLASH (rx) : ORIGIN = 0, LENGTH = 512K  RAM (rwx) : ORIGIN = 0x10000000, LENGTH = 32K }
SECTIONS { .text : { *(.text*) *(.rodata*) } > FLASH  .data : { *(.data*) } > RAM AT > FLASH  .bss : { *(.bss*) *(COMMON) } > RAM
/DISCARD/ : { *(.ARM.exidx*) } }"""
STOP = 0x7FFF0


class Board:
    def __init__(self, src, opt='-Os', extra=()):
        here = os.path.dirname(os.path.abspath(src))
        self.tmp = tempfile.mkdtemp()
        o, elf, bin_ = (os.path.join(self.tmp, n) for n in ('a.o', 'a.elf', 'a.bin'))
        ld = os.path.join(self.tmp, 'a.ld')
        open(ld, 'w').write(LD)
        subprocess.run(['clang', '--target=thumbv7m-none-eabi', '-mcpu=cortex-m3', '-mthumb', opt, '-ffreestanding', '-fno-common',
                        '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-I', here, *extra, '-c', src, '-o', o], check=True)
        subprocess.run(['ld.lld', '-T', ld, '-e', '0', o, '-o', elf], check=True)
        subprocess.run(['llvm-objcopy', '-O', 'binary', '-j', '.text', elf, bin_], check=True)
        self.sym = {}
        for ln in subprocess.run(['llvm-nm', elf], capture_output=True, text=True).stdout.splitlines():
            p = ln.split()
            if len(p) == 3:
                self.sym[p[2]] = int(p[0], 16)
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        for base, size in [(0, 0x80000), (0x10000000, 0x8000), (0x2009C000, 0x4000), (0x40000000, 0x100000), (0xE000E000, 0x1000)]:
            self.mu.mem_map(base, size)
        self.mu.mem_write(0, open(bin_, 'rb').read())
        self.writes = []
        self.mu.hook_add(UC_HOOK_MEM_WRITE, self._w)
        self.on_read = None          # optional: on_read(board, addr) -> value to return, or None (models input pins)
        self.reads = []
        self.mu.hook_add(UC_HOOK_MEM_READ, self._r, begin=0x20000000, end=0xFFFFFFFF)

    def _w(self, uc, access, addr, size, val, ud):
        if addr >= 0x20000000:
            self.writes.append((addr, val & 0xFFFFFFFF))

    def _r(self, uc, access, addr, size, val, ud):
        if self.on_read:
            v = self.on_read(self, addr)
            if v is not None:
                uc.mem_write(addr, struct.pack('<I', v & 0xFFFFFFFF))
                self.reads.append((addr, v & 0xFFFFFFFF))

    def set(self, addr, val):
        self.mu.mem_write(addr, struct.pack('<I', val & 0xFFFFFFFF))

    def get(self, addr):
        return struct.unpack('<I', self.mu.mem_read(addr, 4))[0]

    def call(self, name, *args, count=2_000_000):
        regs = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
        for r, v in zip(regs, args):
            self.mu.reg_write(r, v & 0xFFFFFFFF)
        self.mu.reg_write(UC_ARM_REG_SP, 0x10008000)
        self.mu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.writes = []
        self.mu.emu_start(self.sym[name] | 1, STOP, count=count)
        return self.mu.reg_read(UC_ARM_REG_R0)
