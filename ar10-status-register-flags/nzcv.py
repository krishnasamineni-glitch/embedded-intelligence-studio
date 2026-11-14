#!/usr/bin/env python3
"""nzcv.py - shows the ARM flags N, Z, C, V for a 32-bit ADDS, SUBS or CMP, exactly as the Cortex-M3 sets them.

    python nzcv.py add 0x7FFFFFFF 1
    python nzcv.py sub 3 5
    python nzcv.py                      (all the cases of the video)

C in a subtraction is 1 when there is NO borrow (a - b is done as a + NOT b + 1).
V = carry into bit 31 XOR carry out of bit 31.
"""
import sys

M = 0xFFFFFFFF


def s32(v):
    return v - (1 << 32) if v & 0x80000000 else v


def flags(op, a, b):
    a &= M
    b &= M
    if op == 'add':
        b2, cin = b, 0
    else:                          # sub / cmp
        b2, cin = (~b) & M, 1
    full = a + b2 + cin
    r = full & M
    c = full >> 32
    c_in31 = ((a & 0x7FFFFFFF) + (b2 & 0x7FFFFFFF) + cin) >> 31
    return r, {'N': r >> 31, 'Z': int(r == 0), 'C': c, 'V': c_in31 ^ c}


def show(op, a, b):
    r, f = flags(op, a, b)
    sign = '+' if op == 'add' else '-'
    print(f'0x{a & M:08X} {sign} 0x{b & M:08X} = 0x{r:08X}')
    print(f'  unsigned: {a & M} {sign} {b & M}  ->  {r}')
    print(f'  signed:   {s32(a & M)} {sign} {s32(b & M)}  ->  {s32(r)}')
    print('  N={N} Z={Z} C={C} V={V}'.format(**f))


CASES = [('add', 5, 3), ('add', 0x7FFFFFFF, 1), ('add', 0xFFFFFFFF, 1), ('add', 0x80000000, 0x80000000),
         ('sub', 5, 3), ('sub', 3, 5), ('sub', 5, 5), ('sub', 0x80000000, 1), ('sub', 0xFFFFFFFF, 1),
         ('add', 0x40000000, 0x40000000)]

if __name__ == '__main__':
    if len(sys.argv) == 4:
        show(sys.argv[1].lower().replace('cmp', 'sub'), int(sys.argv[2], 0), int(sys.argv[3], 0))
    else:
        for k, (op, a, b) in enumerate(CASES, 1):
            print(f'case {k}:')
            show(op, a, b)
            print()
