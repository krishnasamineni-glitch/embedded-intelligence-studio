from run_c import Board
N = {0x2009C000: 'FIODIR0', 0x2009C018: 'FIOSET0', 0x2009C01C: 'FIOCLR0', 0x2009C040: 'FIODIR2', 0x2009C058: 'FIOSET2',
     0x2009C05C: 'FIOCLR2', 0x4002C000: 'PINSEL0', 0x4002C010: 'PINSEL4', 0xE000E010: 'SYST_CSR', 0xE000E014: 'SYST_RVR', 0xE000E018: 'SYST_CVR'}
b = Board('sevenseg_demo.c')
b.call('display_setup')
print('setup:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
b.call('show_number', 1234)
d = b.sym['digits']; print('digits:', list(b.mu.mem_read(d, 4)))
for k in range(5):
    b.call('SysTick_Handler')
    print('refresh', k, [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
b.call('show_number', 907); print('907:', list(b.mu.mem_read(d, 4)))
print('E cathode 0x79 -> anode', hex(b.call('anode_code', 0x79)), ' 0 ->', hex(b.call('anode_code', 0x3F)))
# check the segment table against the segment lists
segs = {0: 'abcdef', 1: 'bc', 2: 'abdeg', 3: 'abcdg', 4: 'bcfg', 5: 'acdfg', 6: 'acdefg', 7: 'abc', 8: 'abcdefg', 9: 'abcdfg'}
tab = list(b.mu.mem_read(b.sym['seg'], 10))
for n, sl in segs.items():
    v = sum(1 << 'abcdefg'.index(ch) for ch in sl)
    assert v == tab[n], (n, hex(v), hex(tab[n]))
print('table ok:', [hex(x) for x in tab])
print('E =', hex(sum(1 << 'abcdefg'.index(ch) for ch in 'adefg')))
