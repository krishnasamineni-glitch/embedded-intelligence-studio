# test_lcd.py - run lcd_demo.c on the emulated LPC1768 and decode the pins with a model of the HD44780
from run_c import Board

FIOSET2, FIOCLR2, FIODIR2 = 0x2009C058, 0x2009C05C, 0x2009C040


class HD44780:
    def __init__(self):
        self.pins = 0
        self.four = False          # 8-bit mode after power on
        self.half = None
        self.ddram = [ord(' ')] * 0x80
        self.cgram = [0] * 64
        self.addr, self.cg = 0, False
        self.inc = 1
        self.log = []              # (rs, byte) or ('nib', n)
        self.on = False

    def write(self, addr, v):
        old = self.pins
        if addr == FIOSET2:
            self.pins |= v
        elif addr == FIOCLR2:
            self.pins &= ~v
        if old & 2 and not self.pins & 2:          # E falling edge
            self.latch((old >> 4) & 0xF, old & 1)

    def latch(self, nib, rs):
        if not self.four:
            b = nib << 4                           # 8-bit mode: D7..D4 only, D3..D0 = 0 on our board
            self.log.append(('8-bit', hex(nib)))
            self.exec(b, rs)
            return
        if self.half is None:
            self.half = nib
        else:
            b = self.half << 4 | nib
            self.half = None
            self.log.append(('data' if rs else 'cmd', '0x%02X' % b))
            self.exec(b, rs)

    def exec(self, b, rs):
        if rs:
            if self.cg:
                self.cgram[self.addr & 63] = b
            else:
                self.ddram[self.addr & 0x7F] = b
            self.addr += self.inc
            return
        if b == 0x01:
            self.ddram = [ord(' ')] * 0x80; self.addr = 0; self.cg = False
        elif b & 0x80:
            self.addr = b & 0x7F; self.cg = False
        elif b & 0x40:
            self.addr = b & 0x3F; self.cg = True
        elif b & 0x20:
            self.four = not (b & 0x10)
        elif b & 0x08:
            self.on = bool(b & 4)
        elif b & 0x04:
            self.inc = 1 if b & 2 else -1

    def lines(self):
        f = lambda c: '♥' if c == 0 else chr(c)
        return ''.join(f(c) for c in self.ddram[0:16]), ''.join(f(c) for c in self.ddram[0x40:0x50])


import sys
b = Board('lcd_demo.c', extra=('-DUS_LOOPS=%s' % (sys.argv[1] if len(sys.argv) > 1 else '1'),))
lcd = HD44780()
ins = [0]
from unicorn import UC_HOOK_CODE
b.mu.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ins.__setitem__(0, ins[0] + 1))
pulse = []
def w(uc, access, addr, size, val, ud):
    if addr in (FIOSET2, FIOCLR2):
        if addr == FIOSET2 and val == 2: pulse.append(['E up', ins[0]])
        if addr == FIOCLR2 and val == 2 and pulse: pulse[-1].append(ins[0])
        lcd.write(addr, val)
from unicorn import UC_HOOK_MEM_WRITE
b.mu.hook_add(UC_HOOK_MEM_WRITE, w)
b.call('demo', count=50_000_000)
print('sequence:', lcd.log[:12])
print('total bytes:', len(lcd.log))
l1, l2 = lcd.lines()
print('line 1: [%s]' % l1)
print('line 2: [%s]' % l2)
print('display on:', lcd.on, ' cgram char 0:', [hex(x) for x in lcd.cgram[0:8]])
print('E pulse (instructions high):', min(p[2] - p[1] for p in pulse if len(p) == 3), 'min')
print('writes in demo: PINSEL4/FIODIR2:', [(hex(a), hex(v)) for a, v in b.writes[:3]])
