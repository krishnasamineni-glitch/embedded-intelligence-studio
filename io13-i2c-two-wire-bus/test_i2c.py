# test_i2c.py - i2c_demo.c on the emulated LPC1768 with a model of the I2C2 controller and an LM75 sensor
import sys
from run_c import Board
from unicorn import UC_HOOK_MEM_WRITE
B = 0x400A0000
CONSET, STAT, DAT, SCLH, SCLL, CONCLR = B, B + 4, B + 8, B + 0x10, B + 0x14, B + 0x18
SI, STA, STO, AA, I2EN = 8, 32, 16, 4, 64
LM75 = {'addr': 0x48, 'regs': {0: [0x19, 0x80]}}        # 25.5 degrees
present = [True]
m = {'con': 0, 'stat': 0xF8, 'dat': 0, 'phase': 'idle', 'rw': 0, 'reg': 0, 'rd': [], 'dat_w': False}
bus = []


def ev(code, note):
    m['stat'] = code; m['con'] |= SI; bus.append('%s  -> status 0x%02X' % (note, code))


def step():
    """called when SI is cleared: do the next bus action"""
    if m['con'] & STA:
        ev(0x10 if m['phase'] != 'idle' else 0x08, 'repeated START' if m['phase'] != 'idle' else 'START')
        m['phase'] = 'addr'; return
    if m['phase'] == 'addr' and m['dat_w']:
        a = m['dat']; m['dat_w'] = False; m['rw'] = a & 1
        ok = present[0] and (a >> 1) == LM75['addr']
        if m['rw'] == 0:
            ev(0x18 if ok else 0x20, 'address 0x%02X + W, %s' % (a >> 1, 'ACK' if ok else 'NACK'))
            m['phase'] = 'wdata' if ok else 'dead'
        else:
            ev(0x40 if ok else 0x48, 'address 0x%02X + R, %s' % (a >> 1, 'ACK' if ok else 'NACK'))
            m['phase'] = 'rdata' if ok else 'dead'
            m['rd'] = list(LM75['regs'].get(m['reg'], [0xFF]))
        return
    if m['phase'] == 'wdata' and m['dat_w']:
        m['dat_w'] = False; m['reg'] = m['dat']
        ev(0x28, 'data 0x%02X, ACK' % m['dat']); return
    if m['phase'] == 'rdata':
        byte = m['rd'].pop(0) if m['rd'] else 0xFF
        m['dat'] = byte
        ack = bool(m['con'] & AA)
        ev(0x50 if ack else 0x58, 'slave sends 0x%02X, master %s' % (byte, 'ACK' if ack else 'NACK'))
        return


def w(uc, acc, addr, size, val, ud):
    if addr == CONSET:
        m['con'] |= val
        if val & STA and not (m['con'] & SI) and m['phase'] == 'idle':
            m['con'] &= ~STA; m['con'] |= STA; step()
        if val & STO:
            m['stop_pending'] = True
    elif addr == CONCLR:
        had_si = m['con'] & SI
        m['con'] &= ~val
        if val & SI and had_si:
            if m.get('stop_pending'):
                bus.append('STOP'); m['phase'] = 'idle'; m['stop_pending'] = False; m['con'] &= ~(STO | SI)
            else:
                step()
    elif addr == DAT:
        m['dat'] = val & 0xFF; m['dat_w'] = True


def r(b, addr):
    if addr == CONSET:
        return m['con']
    if addr == STAT:
        return m['stat']
    if addr == DAT:
        return m['dat']
    return None


b = Board('i2c_demo.c')
b.mu.hook_add(UC_HOOK_MEM_WRITE, w)
b.on_read = r
b.set(0x400FC0C4, 0x042887DE)
b.call('i2c_init')
N = {0x400FC0C4: 'PCONP', 0x4002C000: 'PINSEL0', 0x4002C040: 'PINMODE0', 0x4002C068: 'PINMODE_OD0', SCLH: 'I2C2SCLH', SCLL: 'I2C2SCLL',
     CONCLR: 'I2C2CONCLR', CONSET: 'I2C2CONSET'}
print('init:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
v = b.call('lm75_read_half_degrees')
v = v - (1 << 32) if v >> 31 else v
print('\n'.join(bus)); print('half degrees:', v, '->', v / 2, 'C')
bus.clear(); present[0] = False
v = b.call('lm75_read_half_degrees'); v = v - (1 << 32) if v >> 31 else v
print('no sensor:', '\n'.join(bus), v)
