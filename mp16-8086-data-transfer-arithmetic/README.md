# mp16 · 8086 Instruction Set, Part 1: Data Transfer and Arithmetic

Program from the video **8086 Instruction Set Part 1** (MOV rules, PUSH/POP, XCHG, XLAT, LEA, LDS/LES,
ADD … DEC, NEG, CMP, MUL, IMUL, DIV, CBW/CWD, decimal adjust).

| File | What it does |
|---|---|
| `sum5.asm` | Adds five bytes and keeps a 16-bit sum (assembler version) |

## Trainer kit version (as in the video)

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 0100H | `BE 00 05` | `MOV SI, 0500H` | SI → the array |
| 0103H | `B9 05 00` | `MOV CX, 0005H` | count |
| 0106H | `B8 00 00` | `MOV AX, 0000H` | sum = 0 |
| 0109H | `02 04` | `NEXT: ADD AL, [SI]` | add a byte |
| 010BH | `80 D4 00` | `ADC AH, 00H` | add the carry |
| 010EH | `46` | `INC SI` | next byte |
| 010FH | `49` | `DEC CX` | count down |
| 0110H | `75 F7` | `JNZ NEXT` | repeat |
| 0112H | `A3 00 06` | `MOV [0600H], AX` | store the sum |
| 0115H | `F4` | `HLT` | stop |

## Test data

| Address | Value |
|---|---|
| 0500H – 0504H | 7FH 80H FFH 10H 01H |
| 0600H – 0601H | **0FH 02H** → AX = **020FH** (= 527) |

| After byte | AX |
|---|---|
| 7FH, 80H | 00FFH |
| FFH | 01FEH (carry into AH) |
| 10H | 020EH (carry again) |
| 01H | **020FH** |

## XLAT example: 7-segment codes

`BX` = 0200H points to the table, `AL` = 3 → `XLAT` → `AL` = **4FH** (the code for 3).

| Digit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Code | 3FH | 06H | 5BH | 4FH | 66H | 6DH | 7DH | 07H | 7FH | 6FH |

## How to run it

**Assembler version (`.asm`)**: works with EMU8086, MASM and TASM.
In EMU8086: *New* → *empty workspace*, paste the file, press **emulate**, then **run** (or step with
**single step** and watch the registers and memory).
With MASM: `masm file.asm;` → `link file.obj;` → run `file.exe` (or step through it in DEBUG / CodeView).
With TASM: `tasm file.asm` → `tlink file.obj` → run.

**Trainer kit version (the table above)**: enter the code bytes from 0100H, store the input bytes,
run from 0100H, and examine the result. The kit version uses fixed addresses and ends with `HLT`;
the `.asm` version uses names for the data and returns to DOS with `MOV AH, 4CH` / `INT 21H`
(see video mp18).
