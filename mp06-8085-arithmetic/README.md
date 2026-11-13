# mp06 · 8085 Arithmetic Instructions: addition with carry

Programs from the video **8085 Arithmetic Instructions** (ADD, ADC, SUB, SBB, INR, DCR, INX, DCX, DAD, DAA).

| File | What it does |
|---|---|
| `add8_carry.asm` | Adds the bytes at 2050H and 2051H; stores the sum at 2052H and the carry (00H or 01H) at 2053H |
| `add16_dad.asm` | Adds two 16-bit numbers with `DAD D`; stores the 16-bit result at 2054H–2055H |

## Program 1: 8-bit addition with carry

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2000H | `21 50 20` | `LXI H, 2050H` | HL → first number |
| 2003H | `7E` | `MOV A, M` | A = first number |
| 2004H | `23` | `INX H` | HL → second number |
| 2005H | `86` | `ADD M` | A = A + second |
| 2006H | `23` | `INX H` | HL → 2052H |
| 2007H | `77` | `MOV M, A` | store the sum |
| 2008H | `3E 00` | `MVI A, 00H` | A = 0 (flags kept) |
| 200AH | `CE 00` | `ACI 00H` | A = 0 + 0 + CY |
| 200CH | `23` | `INX H` | HL → 2053H |
| 200DH | `77` | `MOV M, A` | store the carry |
| 200EH | `76` | `HLT` | stop |

The trick: `INX`, `MOV` and `MVI` do not change the flags, so the carry from `ADD M` is still there for `ACI 00H`.

| Address | Before | After |
|---|---|---|
| 2050H | 9AH | 9AH |
| 2051H | 87H | 87H |
| 2052H | – | **21H** (sum) |
| 2053H | – | **01H** (carry) |

## Program 2: 16-bit addition with DAD

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 2000H | `2A 50 20` | `LHLD 2050H` | HL = first number |
| 2003H | `EB` | `XCHG` | DE = first number |
| 2004H | `2A 52 20` | `LHLD 2052H` | HL = second number |
| 2007H | `19` | `DAD D` | HL = HL + DE |
| 2008H | `22 54 20` | `SHLD 2054H` | store the result |
| 200BH | `76` | `HLT` | stop |

Test data (low byte first): 2050H–2051H = `34 12` (1234H), 2052H–2053H = `11 11` (1111H)
→ result 2054H–2055H = `45 23` (**2345H**). `DAD` changes only the carry flag.

## How to run it

**On a simulator (e.g. GNUSim8085, free):** type the *instruction* column (labels included), put the
input bytes into memory with the memory editor, run, and look at the result addresses.

**On an 8085 trainer kit:** enter the *code* column byte by byte from the start address, store the input
bytes, run from the start address, then examine the result addresses.
If your kit's user RAM does not start at 2000H (some kits use 8000H or C000H), move the program **and**
change every address inside it: data addresses (2050H …) and jump targets.
