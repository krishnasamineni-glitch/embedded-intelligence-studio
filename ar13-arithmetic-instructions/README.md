# ar13 · ARM Arithmetic Instructions

Every arithmetic instruction of the ARM Cortex-M3 with 32-bit examples: MOV and MVN, the forms of ADD, 64-bit addition with ADDS and ADC, SUB and RSB, 64-bit subtraction with SUBS and SBC, MUL, MLA and MLS, 64-bit products with UMULL and SMULL, the hardware divider UDIV and SDIV with the remainder from MLS, rounding, dividing by zero, and which instructions change the flags. Every value was checked in an ARM emulator.

## Files

* [`arith_demo.s`](arith_demo.s) – every arithmetic example of the video: 64-bit add, multiply, divide, remainder

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Arithmetic instructions  (00:00)

Today: the arithmetic instructions of the ARM Cortex-M3. We will see moves, addition and subtraction, also with 64-bit numbers, multiplication, and the hardware divider, each one with 32-bit examples.

### MOV and MVN  (00:15)

Let's start with moves. MOV R0, R1 copies R1 into R0. MVN, move NOT, copies the inverted value. MVN R0, #0 gives 0xFFFFFFFF, and with R1 equal to 42, MVN R0, R1 gives 0xFFFFFFD5, which is minus 43.

### ADD and its forms  (00:39)

ADD has a few forms. ADD R0, R1, R2 adds two registers: 25 plus 17 gives 42. ADD R0, R1, #100 adds a constant: 25 plus 100 gives 125. And ADD R0, R0, #1 simply increments R0. With ADDS, the flags are updated as well.

### Numbers bigger than 32 bits  (01:01)

What if a number does not fit into 32 bits? Then we keep it in two registers, a low word and a high word, and add in two steps. ADDS adds the low words and puts the carry into C. Then ADC, add with carry, adds the high words plus C.

### 64-bit addition: ADDS + ADC  (01:19)

For example, 0x00000001_FFFFFFFF plus 1. ADDS on the low words gives 0, with C equal to 1. ADC on the high words gives 1 plus 0 plus 1, which is 2. So the 64-bit result is 0x00000002_00000000. The carry has moved from one word to the next.

### SUB and RSB  (01:41)

SUB subtracts: SUB R0, R1, R2 gives R1 minus R2, so 50 minus 8 gives 42. RSB, reverse subtract, swaps the order: RSB R0, R1, #100 gives 100 minus R1. And RSB R0, R1, #0 gives 0 minus R1, which turns 5 into minus 5.

### 64-bit subtraction: SUBS + SBC  (02:03)

64-bit subtraction works the same way. SUBS subtracts the low words and records the borrow in C. Then SBC, subtract with carry, subtracts the high words and the borrow. 0x00000002_00000000 minus 1 gives 0x00000001_FFFFFFFF.

### MUL  (02:22)

MUL multiplies two registers and keeps the lower 32 bits of the product. The Cortex-M3 does this in a single cycle. 1000 times 3000 gives 3 million, which is 0x002DC6C0.

### MLA and MLS  (02:35)

MLA, multiply and accumulate, adds the product to a third register: R0 equals R3 plus R1 times R2. This is the heart of filters and dot products. MLS, multiply and subtract, gives R3 minus R1 times R2.

### 64-bit products: UMULL and SMULL  (02:53)

But the product of two 32-bit numbers can need 64 bits. 0x10000 times 0x10000 is 0x1_00000000, and MUL keeps only the lower word, which is 0. UMULL keeps all 64 bits, in two registers: the low word 0, and the high word 1. SMULL does the same for signed numbers: minus 2 times 3 gives minus 6, which is 0xFFFFFFFF_FFFFFFFA.

### Hardware divide and remainder  (03:25)

The Cortex-M3 has a hardware divider. UDIV divides unsigned numbers, and SDIV signed numbers, in 2 to 12 cycles. UDIV R0, R1, R2 with 100 and 7 gives 14. There is no remainder instruction, but MLS gives it in one step: 100 minus 14 times 7 is 2.

### SDIV rounds towards zero  (03:46)

SDIV rounds towards zero, like C does. Minus 7 divided by 2 gives minus 3. Compare this with ASR, which rounds down, to minus 4.

### Dividing by zero  (03:58)

And dividing by zero? By default, UDIV and SDIV simply return 0, with no error. If we set the DIV_0_TRP bit in the configuration control register, a division by zero causes a UsageFault instead, so the bug can be found.

### Which instructions set the flags  (04:14)

Which instructions change the flags? ADDS, ADCS, SUBS, SBCS and RSBS update N, Z, C and V. A multiply with S updates only N and Z. And UDIV and SDIV never change the flags.

| instruction | flags |
|---|---|
| ADDS  ADCS  SUBS  SBCS  RSBS | N  Z  C  V |
| MULS | N  Z  only |
| UDIV  SDIV | never |
| ADD  SUB  MUL ...  (no S) | unchanged |

### Practice  (04:31)

Now try this yourself. Pause the video. R1 is 50, and R2 is 8. What are R0 and R3 after UDIV R0, R1, R2 and MLS R3, R0, R2, R1? The answers: R0 is 6, the quotient, and R3 is 2, the remainder.

### Summary  (04:53)

Here is the summary. MOV copies and MVN inverts. ADD and SUB come with immediate and register forms, and RSB subtracts the other way round. ADDS with ADC, and SUBS with SBC, handle 64-bit numbers. MUL keeps 32 bits, UMULL and SMULL keep all 64. MLA and MLS multiply and add or subtract. And UDIV and SDIV divide in hardware, with MLS for the remainder.

|   | remember |
|---|---|
| MOV / MVN | copy / copy inverted |
| ADD  SUB  RSB | register or immediate;  RSB = reverse subtract |
| ADDS + ADC,  SUBS + SBC | 64-bit add and subtract |
| MUL / UMULL / SMULL | 32-bit product / full 64-bit product |
| MLA / MLS | multiply and add / subtract |
| UDIV / SDIV | hardware divide;  MLS for the remainder |
