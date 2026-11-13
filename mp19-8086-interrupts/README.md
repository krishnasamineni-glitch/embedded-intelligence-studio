# mp19 · 8086 Interrupts: Vector Table, INT n, IRET and Your Own ISR

Program from the video **8086 Interrupts** (interrupt vector table 00000H–003FFH, type × 4, the stack,
types 0–4, NMI and INTR, priority, installing your own ISR).

| File | What it does |
|---|---|
| `own_isr.asm` | Installs `MYISR` as interrupt type 60H, calls it twice with `INT 60H`, then restores the old vector |

## The idea (as in the video)

```
    MOV AX, 0
    MOV ES, AX
    MOV WORD PTR ES:[180H], OFFSET MYISR   ; vector of type 60H: 60H x 4 = 180H
    MOV WORD PTR ES:[182H], SEG MYISR
    ...
    INT 60H          ; runs MYISR
    ...
MYISR PROC FAR
    ...
    IRET
MYISR ENDP
```

`own_isr.asm` is the complete version: `MYISR` prints a line of text, and the program saves the old
vector first and puts it back before it ends (a good habit).

If your assembler does not accept `SEG MYISR` as an immediate value, use the code segment instead
(MYISR is in it):

```
    MOV AX, CS
    MOV ES:[182H], AX
```

## Quick reference

| Item | Value |
|---|---|
| Vector table | 256 vectors × 4 bytes, 00000H – 003FFH |
| Vector of type n | at n × 4: IP first, then CS |
| `INT n` | pushes FLAGS, CS, IP (6 bytes); clears IF and TF |
| `IRET` | pops IP, CS, FLAGS |
| Types 0 – 4 | divide error, single step, NMI, breakpoint (INT 3), overflow (INTO) |

## How to run it

In EMU8086: *New* → *empty workspace*, paste `own_isr.asm`, press **emulate**, then **run**:
the line *Hello from MYISR (type 60H)* appears twice.
With MASM: `masm own_isr.asm;` → `link own_isr.obj;` → `own_isr`.
