from run_c import Board
b = Board('dac_demo.c')
b.call('dac_setup'); print('setup', [(hex(a), '0x%08X' % v) for a, v in b.writes])
for mv in (1650, 1000, 3300, 0):
    n = b.call('dac_value_for_mv', mv); b.call('dac_write', n)
    print(f'{mv} mV -> value {n} -> DACR 0x{b.writes[-1][1]:08X} -> Vout {n * 3.3 / 1024:.4f} V')
b.call('dac_write', 1023); print('1023 ->', '0x%08X' % b.writes[-1][1], 1023 * 3.3 / 1024)
s = []
for i in range(34):
    b.call('dac_next_sample'); s.append(b.writes[-1][1] >> 6)
print('samples:', s)
print('DACR first 4:', ['0x%08X' % (v << 6) for v in s[:4]], ' peak', '0x%08X' % (1023 << 6))
