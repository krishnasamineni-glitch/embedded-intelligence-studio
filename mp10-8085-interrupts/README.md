# mp10 · 8085 Interrupts, SIM and RIM: counting RST 7.5 pulses

Program from the video **8085 Interrupts** (TRAP, RST 7.5/6.5/5.5, INTR, vectors, priority, SIM and RIM).

| File | What it does |
|---|---|
| `rst75_counter.asm` | Enables only RST 7.5 with `SIM`; every RST 7.5 pulse runs the ISR, which adds 1 to the counter at 2050H |

## Main program (2000H)

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2000H | `31 FF 2F` | `LXI SP, 2FFFH` | stack |
| 2003H | `3E 0B` | `MVI A, 0BH` | only RST 7.5 |
| 2005H | `30` | `SIM` |  |
| 2006H | `FB` | `EI` |  |
| 2007H | `C3 07 20` | `LOOP: JMP LOOP` | wait |

## Vector (003CH)

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 003CH | `C3 00 21` | `JMP 2100H` | to the ISR |

## Interrupt service routine (2100H)

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2100H | `F5` | `PUSH PSW` | save A + flags |
| 2101H | `E5` | `PUSH H` | save HL |
| 2102H | `21 50 20` | `LXI H, 2050H` |  |
| 2105H | `34` | `INR M` | count |
| 2106H | `E1` | `POP H` | restore |
| 2107H | `F1` | `POP PSW` |  |
| 2108H | `FB` | `EI` |  |
| 2109H | `C9` | `RET` | back |

`PUSH PSW` / `PUSH H` save A, the flags and HL, so the main program finds them unchanged.
`EI` is needed again before `RET`, because accepting an interrupt disables further interrupts.

## SIM byte

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|---|
| Name | SOD | SDE | × | R7.5 | MSE | M7.5 | M6.5 | M5.5 |
| 0BH | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |

## On a trainer kit

Address 003CH is inside the kit's monitor ROM, so you cannot write `JMP 2100H` there.
Most kits' monitors jump from 003CH to a fixed RAM address: look it up in your kit's manual and put
`JMP 2100H` (or the ISR itself) at that RAM address. Clear 2050H, run from 2000H, apply pulses to the
RST 7.5 pin, then stop and examine 2050H.
