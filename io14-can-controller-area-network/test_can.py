from run_c import Board
N = {0x400FC0C4: 'PCONP', 0x4002C000: 'PINSEL0', 0x40044000: 'CAN1MOD', 0x40044014: 'CAN1BTR', 0x4003C000: 'AFMR', 0x40044030: 'CAN1TFI1',
     0x40044034: 'CAN1TID1', 0x40044038: 'CAN1TDA1', 0x4004403C: 'CAN1TDB1', 0x40044004: 'CAN1CMR'}
b = Board('can_demo.c')
b.on_read = lambda bb, a: 0x0C if a == 0x4004401C else None     # status: TBS1 = 1
b.set(0x400FC0C4, 0x042887DE)
b.call('can1_init_500k'); print('init:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])
btr = b.get(0x40044014)
brp = (btr & 0x3FF) + 1; sjw = (btr >> 14 & 3) + 1; t1 = (btr >> 16 & 15) + 1; t2 = (btr >> 20 & 7) + 1
tq = 1 + t1 + t2
print('BRP', brp, 'TSEG1', t1, 'TSEG2', t2, 'SJW', sjw, '-> bit rate', 25e6 / brp / tq, 'sample point', (1 + t1) / tq)
b.call('send_rpm', 3000); print('send:', [(N.get(a, hex(a)), '0x%08X' % v) for a, v in b.writes])


def crc15(bits):
    crc = 0
    for bt in bits:
        nxt = bt ^ ((crc >> 14) & 1)
        crc = (crc << 1) & 0x7FFF
        if nxt:
            crc ^= 0x4599
    return crc


def frame(idv, data):
    bits = [0] + [idv >> (10 - k) & 1 for k in range(11)] + [0, 0, 0] + [len(data) >> (3 - k) & 1 for k in range(4)]
    for byte in data:
        bits += [byte >> (7 - k) & 1 for k in range(8)]
    c = crc15(bits)
    bits += [c >> (14 - k) & 1 for k in range(15)]
    stuffed, run, last = [], 0, None
    nst = 0
    for bt in bits:
        stuffed.append(bt)
        run = run + 1 if bt == last else 1
        last = bt
        if run == 5:
            stuffed.append(1 - bt); nst += 1; last = 1 - bt; run = 1
    return bits, c, stuffed, nst


bits, c, st, nst = frame(0x123, [0x0B, 0xB8])
print('CRC 0x%04X' % c, 'bits before stuffing', len(bits), 'stuff bits', nst, 'total with CRC del, ACK, EOF', len(st) + 1 + 2 + 7)
for a, bb in ((0x123, 0x125), (0x100, 0x0FF)):
    for k in range(11):
        x, y = a >> (10 - k) & 1, bb >> (10 - k) & 1
        if x != y:
            print(hex(a), 'vs', hex(bb), 'differ at id bit', 10 - k, '->', hex(a if x == 0 else bb), 'wins'); break
