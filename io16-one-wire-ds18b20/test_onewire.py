# test_onewire.py - onewire_demo.c on the emulated LPC1768 with a time model of the 1-Wire line and a DS18B20
from run_c import Board
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC

FIODIR0, FIOPIN0 = 0x2009C000, 0x2009C014
DQ = 1 << 4


def crc8(data):
    crc = 0
    for b in data:
        for _ in range(8):
            m = (crc ^ b) & 1
            crc >>= 1
            if m:
                crc ^= 0x8C
            b >>= 1
    return crc


SCR = [0x91, 0x01, 0x4B, 0x46, 0x7F, 0xFF, 0x0F, 0x10]
SCR.append(crc8(SCR))
st = {'t': 0.0, 'low': False, 'fall': 0.0, 'hold_until': -1, 'mode': 'idle', 'bits': [], 'send': [], 'busy': 3, 'present': True,
      'log': [], 'min_pulse': {}}


def slave_release(dur):
    m = st['mode']
    if dur >= 480:
        if st['present']:
            st['presence'] = (st['t'] + 30, st['t'] + 150)
            st['mode'] = 'rom'; st['bits'] = []
            st['log'].append('reset %.0f us -> presence' % dur)
        return
    if m in ('rom', 'func'):
        bit = 1 if dur < 15 else 0
        st['bits'].append(bit)
        if len(st['bits']) == 8:
            v = sum(b << i for i, b in enumerate(st['bits']))
            st['bits'] = []
            st['log'].append('%s command 0x%02X' % ('ROM' if m == 'rom' else 'function', v))
            if m == 'rom':
                st['mode'] = 'func'
            elif v == 0x44:
                st['mode'] = 'convert'
            elif v == 0xBE:
                st['mode'] = 'send'
                st['send'] = [b >> i & 1 for b in SCR for i in range(8)]


def slave_fall():
    """falling edge from the master: in read modes, decide what to send"""
    m = st['mode']
    if m == 'convert':
        if st['busy'] > 0:
            st['busy'] -= 1; st['hold_until'] = st['t'] + 30
        else:
            st['hold_until'] = -1
    elif m == 'send' and st['send']:
        b = st['send'].pop(0)
        st['hold_until'] = st['t'] + 30 if b == 0 else -1


def line_level():
    t = st['t']
    if st['low']:
        return 0
    if t < st['hold_until']:
        return 0
    pr = st.get('presence')
    if pr and pr[0] <= t < pr[1]:
        return 0
    return 1


def on_write(uc, acc, addr, size, val, ud):
    if addr != FIODIR0:
        return
    low = bool(val & DQ)
    if low and not st['low']:
        st['low'] = True; st['fall'] = st['t']; slave_fall()
    elif not low and st['low']:
        st['low'] = False
        dur = st['t'] - st['fall']
        kind = 'reset' if dur >= 480 else ('long' if dur >= 60 else 'short')
        st['min_pulse'][kind] = min(st['min_pulse'].get(kind, 1e9), dur)
        slave_release(dur)


b = Board('onewire_demo.c')
DELAY = b.sym['delay_us']


def on_code(uc, addr, size, ud):
    if addr == DELAY:
        st['t'] += uc.reg_read(UC_ARM_REG_R0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)


b.mu.hook_add(UC_HOOK_CODE, on_code, begin=DELAY, end=DELAY)
b.mu.hook_add(UC_HOOK_MEM_WRITE, on_write)
b.on_read = lambda bb, a: (0xFFFFFFFF if line_level() else ~DQ & 0xFFFFFFFF) if a == FIOPIN0 else None
b.call('ow_init')
v = b.call('ds18b20_read_temp16', count=20_000_000)
v = v - (1 << 32) if v >> 31 else v
print('\n'.join(st['log']))
print('result', v, '/16 =', v / 16, 'C;   scratchpad CRC 0x%02X' % SCR[8], '; total time %.1f ms' % (st['t'] / 1000))
print('shortest pulses:', st['min_pulse'])
st.update({'present': False, 'mode': 'idle', 'log': [], 'presence': None})
v = b.call('ds18b20_read_temp16', count=20_000_000); v = v - (1 << 32) if v >> 31 else v
print('no sensor ->', v)
