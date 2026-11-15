# test_keypad.py - run keypad_demo.c on the emulated LPC1768 with a model of the 4x4 key matrix
from run_c import Board

FIO2DIR, FIO2PIN = 0x2009C040, 0x2009C054
pressed = set()                          # {(row, col)}
log = []


def pins(b, addr):
    if addr != FIO2PIN:
        return None
    d = b.get(FIO2DIR)
    low = {('r', r) for r in range(4) if d >> r & 1}          # driven rows (latch 0)
    rowdir = [d >> r & 1 for r in range(4)]
    log.append(rowdir)
    changed = True
    while changed:                       # spread "low" through the pressed keys
        changed = False
        for (r, c) in pressed:
            a, bb = ('r', r), ('c', c)
            if (a in low) != (bb in low):
                low |= {a, bb}
                changed = True
    v = 0xFFFFFFFF
    for r in range(4):
        if ('r', r) in low: v &= ~(1 << r)
    for c in range(4):
        if ('c', c) in low: v &= ~(1 << (4 + c))
    return v


b = Board('keypad_demo.c')
b.on_read = pins
b.set(0x4002C010, 0xFFFFFFFF); b.set(0x4002C050, 0xFFFFFFFF); b.set(FIO2DIR, 0xFFFFFFFF)
b.call('keypad_setup')
print('setup:', [(hex(a), hex(v)) for a, v in b.writes])

def scan():
    log.clear()
    k = b.call('keypad_scan')
    k = k - (1 << 32) if k >> 31 else k
    return k

pressed.clear(); print('none ->', scan())
pressed.add((1, 2)); k = scan(); print('key 6 (row1,col2) ->', k, chr(b.call('key_char', k)), 'rows driven per read:', log)
# columns read when row 1 is low
b.reads = []; scan(); print('reads:', [hex(v) for a, v in b.reads])
pressed.clear(); pressed.add((2, 1)); print('row2,col1 ->', scan(), chr(b.call('key_char', scan())))
pressed.clear(); pressed.add((3, 3)); print('D ->', chr(b.call('key_char', scan())))
pressed.clear(); pressed.add((1, 3)); print('B ->', scan(), chr(b.call('key_char', scan())))
# ghosting: keys (0,0), (0,2), (2,0) pressed -> scanning row 2 also sees column 2 => ghost key (2,2) = '9'
pressed.clear(); pressed |= {(0, 0), (0, 2), (2, 0)}
for r in range(4):
    pass
# read columns per row
def cols_per_row():
    out = {}
    for r in range(4):
        b.set(FIO2DIR, 1 << r)
        out[r] = None
    return out
# direct model check for the ghost
import itertools
for r in range(4):
    b.set(FIO2DIR, 1 << r)
    v = pins(b, FIO2PIN)
    print(' row', r, 'low -> columns', format((v >> 4) & 0xF, '04b')[::-1], '(C0..C3)')
# debouncing with a bouncing press of '5' (row 1, col 1)
b.call('keypad_setup')
seq = [None, None, (1, 1), None, (1, 1), (1, 1), None, (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1),
       None, (1, 1), None, None, None, None, None, None, (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)]
ev = []
for s_ in seq:
    pressed.clear()
    if s_: pressed.add(s_)
    e = b.call('key_event'); e = e - (1 << 32) if e >> 31 else e
    ev.append(e)
print('samples:', ''.join('1' if s_ else '0' for s_ in seq))
print('events :', ev)
