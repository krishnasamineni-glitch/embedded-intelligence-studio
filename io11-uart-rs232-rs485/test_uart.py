# test_uart.py - run uart_demo.c on the emulated LPC1768 with a model of UART0
from run_c import Board
from unicorn import UC_HOOK_MEM_WRITE
B = 0x4000C000
N = {B: 'U0THR/U0DLL', B + 4: 'U0DLM', B + 8: 'U0FCR', B + 0xC: 'U0LCR', B + 0x28: 'U0FDR', 0x4002C000: 'PINSEL0'}
lcr = [0]; tx = []; rx = []; busy = [0]


def w(uc, acc, addr, size, val, ud):
    if addr == B + 0xC:
        lcr[0] = val
    elif addr == B and not (lcr[0] & 0x80):
        tx.append(val & 0xFF); busy[0] = 2        # transmitter busy for two status reads


def r(b, addr):
    if addr == B + 0x14:                          # U0LSR
        thre = 0
        if busy[0]:
            busy[0] -= 1
        else:
            thre = 0x60
        return thre | (1 if rx else 0)
    if addr == B and not (lcr[0] & 0x80):        # U0RBR
        return rx.pop(0) if rx else 0
    return None


b = Board('uart_demo.c')
b.mu.hook_add(UC_HOOK_MEM_WRITE, w)
b.on_read = r
b.call('hello')
print('writes:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes][:7])
print('sent:', bytes(tx), [hex(x) for x in tx])
tx.clear()
b.call('uart0_init_115200'); print('115200:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
rx.extend(b'abc!'); tx.clear()
b.call('uart0_echo_upper', 4); print('echo:', bytes(tx))
for div, fr in ((163, 1.0), (14, 1.0), (9, 1.5)):
    baud = 25e6 / (16 * div * fr); print(div, fr, round(baud), 'error %.2f %%' % ((baud / (9600 if div == 163 else 115200) - 1) * 100))
