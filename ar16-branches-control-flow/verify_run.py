# verify_run.py - runs a whole Keil-syntax Thumb-2 program (branches, loops, calls) in an emulator and checks the
# comments: "flags: N=. Z=. C=. V=.", "Rn = 0x........" and "Rn = <decimal>".
# A comment on an instruction is checked each time execution reaches the instruction that follows it in memory
# (for BL: when the call returns); a comment on a label line is checked when execution reaches the label.
# The last check of each comment counts (so a comment inside a loop is checked after the last pass).
import re
import sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_V8
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *

ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_V8)
REG = {f'R{i}': globals()[f'UC_ARM_REG_R{i}'] for i in range(13)}
src = open(sys.argv[1]).read().splitlines()

out, checks, entry = [], [], None
for n, ln in enumerate(src):
    code, _, com = ln.partition(';')
    code = code.rstrip()
    if not code.strip():
        continue
    first = code.split()[0]
    if first in ('AREA', 'THUMB', 'EXPORT', 'END'):
        continue
    lab = None
    if not code[0].isspace():                       # a label in column 0
        lab = first
        out.append(f'{lab}:')
        entry = entry or lab
        code = code[len(first):]
        if not code.strip():
            if re.search(r'R\d+ = |flags:', com):
                out.append(f'__L{n}:')
                checks.append((n, 'label', com))
            continue
    code = code.strip()
    op = code.split()[0].upper()
    m = re.match(r'LDR\s+(R\d+),\s*=(0x[0-9A-Fa-f]+)', code)
    if m:
        v = int(m.group(2), 16)
        code = f'movw {m.group(1)}, #{v & 0xFFFF}\nmovt {m.group(1)}, #{v >> 16}'
    elif op == 'DCB':
        code = '.byte ' + code[3:].strip()
    elif op == 'ALIGN':
        code = '.balign ' + (code[5:].strip() or '4')
    has = bool(re.search(r'R\d+ = |flags:', com))
    if has:
        out.append(f'__S{n}:')
    out.append(code)
    if has:
        out.append(f'__E{n}:')
        checks.append((n, 'insn', com))

table = ['.balign 4', '__table:'] + [f'.word {"__L" if k == "label" else "__S"}{n}' for n, k, _ in checks] + \
        [f'.word __E{n}' for n, k, _ in checks if k == 'insn']
BASE = 0x10000
enc, _ = ks.asm('\n'.join(out + table), BASE)
img = bytes(enc)
nw = len(checks) + sum(1 for c in checks if c[1] == 'insn')
words = [int.from_bytes(img[len(img) - 4 * nw + 4 * i:len(img) - 4 * nw + 4 * i + 4], 'little') for i in range(nw)]
first_addr, end_addr, k2 = {}, {}, len(checks)
ei = 0
for i, (n, kind, com) in enumerate(checks):
    if kind == 'label':
        end_addr.setdefault(words[i], []).append((n, com, True))
    else:
        first_addr.setdefault(words[i], []).append(n)
        end_addr.setdefault(words[k2 + ei], []).append((n, com, False))
        ei += 1

mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
mu.mem_map(BASE, 0x10000)
mu.mem_map(0x20000000, 0x100000)                     # RAM, also for 0x2007C000
mu.mem_map(0x10000000, 0x10000)                      # stack
mu.mem_write(BASE, img)
STOP = BASE + 0x8000
mu.reg_write(UC_ARM_REG_SP, 0x10008000)
mu.reg_write(UC_ARM_REG_LR, STOP | 1)
pending, last = set(), {}


def hook(uc, addr, size, _):
    for n, com, always in end_addr.get(addr, []):
        if always or n in pending:
            pending.discard(n)
            cpsr = uc.reg_read(UC_ARM_REG_CPSR)
            fl = {'N': cpsr >> 31 & 1, 'Z': cpsr >> 30 & 1, 'C': cpsr >> 29 & 1, 'V': cpsr >> 28 & 1}
            errs = []
            m = re.search(r'flags:\s*N=(\d) Z=(\d) C=(\d) V=(\d)', com)
            if m and dict(zip('NZCV', map(int, m.groups()))) != fl:
                errs.append(f'flags {fl}')
            for r, v in re.findall(r'(R\d+) = (0x[0-9A-Fa-f]{8}|-?\d+)(?![\dxA-Fa-f])', com):
                want = int(v, 16) if v.startswith('0x') else int(v) & 0xFFFFFFFF
                got = uc.reg_read(REG[r])
                if got != want:
                    errs.append(f'{r}={hex(got)}')
            last[n] = errs
    for n in first_addr.get(addr, []):
        pending.add(n)


mu.hook_add(UC_HOOK_CODE, hook)
mu.emu_start(BASE | 1, STOP, count=100000)
bad = 0
for n, kind, com in checks:
    if n not in last:
        print(f'line {n + 1}: never checked: {src[n].strip()}'); bad += 1
    elif last[n]:
        print(f'line {n + 1}: MISMATCH {last[n]}: {src[n].strip()}'); bad += 1
print(sys.argv[1], 'ran to the end;', len(checks), 'comments checked,', bad, 'problems')
