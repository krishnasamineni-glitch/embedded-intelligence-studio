# test_spi.py - spi_demo.c on the emulated LPC1768 with a model of the SPI block and of a SPI flash
from run_c import Board
from unicorn import UC_HOOK_MEM_WRITE
SPCR, SPSR, SPDR, SPCCR = 0x40020000, 0x40020004, 0x40020008, 0x4002000C
FIOSET0, FIOCLR0 = 0x2009C018, 0x2009C01C
st = {'cs': 1, 'rx': 0, 'done': 0, 'n': 0}
log = []
ANSWER = [0xEF, 0x40, 0x18]


def flash(byte_in):
    k = st['n']; st['n'] += 1
    if k == 0:
        st['cmd'] = byte_in; return 0xFF
    if st.get('cmd') == 0x9F and 1 <= k <= 3:
        return ANSWER[k - 1]
    return 0xFF


def w(uc, acc, addr, size, val, ud):
    if addr == FIOCLR0 and val & (1 << 16):
        st['cs'] = 0; st['n'] = 0; log.append('CS low')
    elif addr == FIOSET0 and val & (1 << 16):
        st['cs'] = 1; log.append('CS high')
    elif addr == SPDR:
        out = val & 0xFF
        inp = flash(out) if st['cs'] == 0 else 0xFF
        st['rx'] = inp; st['done'] = 1
        log.append('MOSI 0x%02X  MISO 0x%02X' % (out, inp))


def r(b, addr):
    if addr == SPSR:
        return 0x80 if st['done'] else 0
    if addr == SPDR:
        st['done'] = 0
        return st['rx']
    return None


b = Board('spi_demo.c')
b.mu.hook_add(UC_HOOK_MEM_WRITE, w)
b.on_read = r
b.call('spi_init')
N = {0x4002C000: 'PINSEL0', 0x4002C004: 'PINSEL1', 0x2009C000: 'FIODIR0', FIOSET0: 'FIOSET0', SPCCR: 'S0SPCCR', SPCR: 'S0SPCR'}
print('init:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
log.clear()
idv = b.call('flash_read_id')
print('id = 0x%06X' % idv)
print('\n'.join(log))
