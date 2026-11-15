# test_adc.py - run adc_demo.c on the emulated LPC1768 with a model of the 12-bit ADC
from run_c import Board
import random
AD0CR, AD0GDR = 0x40034000, 0x40034004
VIN = [2.0]
noise = [0.0]
state = {'polls': 0}


def adc(b, addr):
    if addr != AD0GDR:
        return None
    cr = b.get(AD0CR)
    if (cr >> 24) & 7 != 1 or not (cr >> 21) & 1:
        return 0
    state['polls'] += 1
    if state['polls'] < 3:                    # busy for a while
        return 0
    v = VIN[0] + random.gauss(0, noise[0])
    n = max(0, min(4095, int(v / 3.3 * 4096)))
    return (1 << 31) | ((cr & 0xFF).bit_length() - 1) << 24 | n << 4


b = Board('adc_demo.c')
b.on_read = adc
b.set(0x400FC0C4, 0x042887DE)               # PCONP reset value: ADC (bit 12) off
b.call('adc_setup')
N = {0x400FC0C4: 'PCONP', 0x4002C004: 'PINSEL1', 0x4002C044: 'PINMODE1', AD0CR: 'AD0CR'}
print('setup:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
for v in (2.0, 1.65, 0.25, 3.3, 0.0):
    VIN[0] = v; state['polls'] = 0
    n = b.call('adc_read')
    print(f'Vin {v} V -> N = {n}, mV = {b.call("adc_millivolts", n)}, GDR read = {[hex(x) for a, x in b.reads[-1:]]}')
    if v == 2.0:
        print('   writes during read:', [(N.get(a, hex(a)), '0x%08X' % x) for a, x in b.writes])
random.seed(1); noise[0] = 0.004; VIN[0] = 1.0
singles = []
for k in range(8):
    state['polls'] = 0; singles.append(b.call('adc_read'))
print('noisy single readings at 1.0 V:', singles, ' ideal', int(1.0 / 3.3 * 4096))
class P(dict): pass
def adc2(bb, addr):
    state['polls'] = 5
    return adc(bb, addr)
b.on_read = adc2
avg = [b.call('adc_read_avg16', count=5_000_000) for k in range(8)]
print('averaged:', avg)
