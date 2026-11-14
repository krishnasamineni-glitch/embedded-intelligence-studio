#!/usr/bin/env python3
"""alias_calc.py - bit-band alias address calculator for the ARM Cortex-M3.

    python alias_calc.py 0x20000300 2        -> 0x22006008
    python alias_calc.py 0x2009C014 22       -> 0x233802D8   (LPC1768 FIO0PIN, P0.22)

alias = alias base + (address - region base) x 32 + bit x 4
"""
import sys

REGIONS = [(0x20000000, 0x200FFFFF, 0x22000000, 'SRAM'), (0x40000000, 0x400FFFFF, 0x42000000, 'peripheral')]


def alias(addr, bit):
    if not 0 <= bit <= 31:
        raise ValueError('bit must be 0 .. 31')
    for lo, hi, base, name in REGIONS:
        if lo <= addr <= hi:
            off = addr - lo
            a = base + off * 32 + bit * 4
            print(f'{name} bit-band region: offset = 0x{off:X}')
            print(f'  0x{base:08X} + 0x{off:X} x 32 (0x{off * 32:X}) + {bit} x 4 (0x{bit * 4:X})  =  0x{a:08X}')
            return a
    raise ValueError(f'0x{addr:08X} is not in a bit-band region (only the first 1 MB of SRAM and of peripherals)')


if __name__ == '__main__':
    if len(sys.argv) == 3:
        alias(int(sys.argv[1], 0), int(sys.argv[2], 0))
    else:
        for a, b in [(0x20000300, 2), (0x2009C014, 22), (0x20000004, 7), (0x40004000, 0)]:
            print(f'address 0x{a:08X}, bit {b}:')
            alias(a, b)
            print()
