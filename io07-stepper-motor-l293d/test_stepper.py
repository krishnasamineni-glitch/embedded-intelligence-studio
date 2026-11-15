from run_c import Board
N = {0x2009C058: 'FIOSET2', 0x2009C05C: 'FIOCLR2', 0x2009C040: 'FIODIR2', 0x4002C010: 'PINSEL4'}
b = Board('stepper_demo.c', extra=('-DUS_LOOPS=0',))
pins = [0]
def apply(ws):
    out = []
    for a, v in ws:
        if a == 0x2009C058: pins[0] |= v
        if a == 0x2009C05C: pins[0] &= ~v
        if a in (0x2009C058, 0x2009C05C): out.append(pins[0] & 0xF)
    return out
b.call('stepper_setup'); print('setup', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes], 'pins', apply(b.writes))
fw = []
for k in range(4):
    b.call('step', 1); w = [(N[a], '0x%08X' % v) for a, v in b.writes]; seq = apply(b.writes); fw.append(hex(seq[-1])); print('fwd', w, [hex(x) for x in seq])
print('forward:', fw)
bw = []
for k in range(4):
    b.call('step', -1 & 0xFFFFFFFF); bw.append(hex(apply(b.writes)[-1]))
print('backward:', bw)
b.call('rotate', 3, 1, 5); print('rotate 3 writes', len(b.writes), [hex(x) for x in apply(b.writes)][1::2])
print('half:', [hex((lambda: (b.call('half_step_to', k), apply(b.writes)[-1])[1])()) for k in range(8)])
b.call('release'); print('release', [(N[a], '0x%08X' % v) for a, v in b.writes])
