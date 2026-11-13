# mp07 · 8085 Logical and Rotate Instructions: nibble program

Program from the video **8085 Logical and Rotate Instructions** (ANA, ORA, XRA, CMA, CMP, RLC, RRC, RAL, RAR).

| File | What it does |
|---|---|
| `nibbles.asm` | Splits the byte at 2050H: lower nibble → 2051H, upper nibble → 2052H |

## The program

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2000H | `3A 50 20` | `LDA 2050H` | A = A7H |
| 2003H | `E6 0F` | `ANI 0FH` | keep the lower nibble |
| 2005H | `32 51 20` | `STA 2051H` | store 07H |
| 2008H | `3A 50 20` | `LDA 2050H` | A = A7H again |
| 200BH | `E6 F0` | `ANI F0H` | keep the upper nibble |
| 200DH | `0F` | `RRC` |  |
| 200EH | `0F` | `RRC` |  |
| 200FH | `0F` | `RRC` |  |
| 2010H | `0F` | `RRC` | 4 × right |
| 2011H | `32 52 20` | `STA 2052H` | store 0AH |
| 2014H | `76` | `HLT` | stop |

`ANI 0FH` keeps the lower four bits; `ANI F0H` keeps the upper four bits, and four `RRC`s move them down.

| Address | Before | After |
|---|---|---|
| 2050H | A7H | A7H |
| 2051H | – | **07H** |
| 2052H | – | **0AH** |

## How to run it

**On a simulator (e.g. GNUSim8085, free):** type the *instruction* column (labels included), put the
input bytes into memory with the memory editor, run, and look at the result addresses.

**On an 8085 trainer kit:** enter the *code* column byte by byte from the start address, store the input
bytes, run from the start address, then examine the result addresses.
If your kit's user RAM does not start at 2000H (some kits use 8000H or C000H), move the program **and**
change every address inside it: data addresses (2050H …) and jump targets.
