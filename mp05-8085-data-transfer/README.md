# mp05 · 8085 Data Transfer Instructions: swap program

Program from the video **8085 Data Transfer Instructions** (MOV, MVI, LXI, LDA/STA, LHLD/SHLD, LDAX/STAX, XCHG, IN/OUT).

| File | What it does |
|---|---|
| `swap.asm` | Swaps the two bytes at 2050H and 2051H, using register B as a temporary store |

## The program

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2000H | `3A 50 20` | `LDA 2050H` | A = first byte |
| 2003H | `47` | `MOV B, A` | keep it in B |
| 2004H | `3A 51 20` | `LDA 2051H` | A = second byte |
| 2007H | `32 50 20` | `STA 2050H` | second → first place |
| 200AH | `78` | `MOV A, B` | A = first byte again |
| 200BH | `32 51 20` | `STA 2051H` | first → second place |
| 200EH | `76` | `HLT` | stop |

## Test data

| Address | Before | After |
|---|---|---|
| 2050H | 11H | **22H** |
| 2051H | 22H | **11H** |

Data transfer instructions do not change any flag.

## How to run it

**On a simulator (e.g. GNUSim8085, free):** type the *instruction* column (labels included), put the
input bytes into memory with the memory editor, run, and look at the result addresses.

**On an 8085 trainer kit:** enter the *code* column byte by byte from the start address, store the input
bytes, run from the start address, then examine the result addresses.
If your kit's user RAM does not start at 2000H (some kits use 8000H or C000H), move the program **and**
change every address inside it: data addresses (2050H …) and jump targets.
