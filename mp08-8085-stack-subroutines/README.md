# mp08 · 8085 Jumps, Loops, Stack and Subroutines: largest number

Program from the video **8085 Stack and Subroutines** (JMP, JZ/JNZ, JC/JNC, loops, PUSH, POP, CALL, RET, RST).

| File | What it does |
|---|---|
| `largest.asm` | Finds the largest of N bytes (N at 2050H, the bytes from 2051H) and stores it at 2060H |

## The program

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2000H | `21 50 20` | `LXI H, 2050H` | HL → the list |
| 2003H | `4E` | `MOV C, M` | C = count |
| 2004H | `23` | `INX H` |  |
| 2005H | `7E` | `MOV A, M` | A = first number |
| 2006H | `0D` | `DCR C` | one number used |
| 2007H | `23` | `LOOP: INX H` | next number |
| 2008H | `BE` | `CMP M` | A − M, flags only |
| 2009H | `D2 0D 20` | `JNC SKIP` | no carry: A ≥ M |
| 200CH | `7E` | `MOV A, M` | new largest |
| 200DH | `0D` | `SKIP: DCR C` |  |
| 200EH | `C2 07 20` | `JNZ LOOP` | repeat |
| 2011H | `32 60 20` | `STA 2060H` | store the result |
| 2014H | `76` | `HLT` | stop |

## Test data

| Address | Value | |
|---|---|---|
| 2050H | 05H | count |
| 2051H – 2055H | 23H 8AH 45H 9CH 61H | the numbers |
| 2060H | **9CH** | result |

| Step | HL | M | CY | A | C |
|---|---|---|---|---|---|
| start | 2051H | 23H | – | 23H | 04H |
| pass 1 | 2052H | 8AH | 1 | 8AH | 03H |
| pass 2 | 2053H | 45H | 0 | 8AH | 02H |
| pass 3 | 2054H | 9CH | 1 | 9CH | 01H |
| pass 4 | 2055H | 61H | 0 | 9CH | 00H |

The numbers are treated as unsigned bytes (00H–FFH).

## How to run it

**On a simulator (e.g. GNUSim8085, free):** type the *instruction* column (labels included), put the
input bytes into memory with the memory editor, run, and look at the result addresses.

**On an 8085 trainer kit:** enter the *code* column byte by byte from the start address, store the input
bytes, run from the start address, then examine the result addresses.
If your kit's user RAM does not start at 2000H (some kits use 8000H or C000H), move the program **and**
change every address inside it: data addresses (2050H …) and jump targets.
