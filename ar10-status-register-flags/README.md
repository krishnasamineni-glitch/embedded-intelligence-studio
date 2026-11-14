# ar10 · ARM Status Register Flags Explained

When exactly does a carry or an overflow happen in a 32-bit ARM processor? We explain the status register (APSR) flag by flag: N, Z, C, V and Q, and the S suffix. We work through 32-bit cases: addition with and without carry and overflow, subtraction where C = 1 means no borrow (the opposite of Intel processors), signed and unsigned comparison with CMP, the condition codes, logical and shift instructions, saturation with SSAT, and why there is no parity flag.

## Files

* [`flags_demo.s`](flags_demo.s) – all the cases of the video in Cortex-M3 assembly: step through and watch N Z C V
* [`nzcv.py`](nzcv.py) – calculator: N, Z, C, V for any 32-bit ADDS / SUBS / CMP

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### The status register  (00:00)

Today: the status register of the Cortex-M3, and its flags N, Z, C, V and Q. We will work through many cases, for addition, subtraction, compare, shifts and saturation. And we will see how the flags decide signed and unsigned comparisons.

### APSR: the flag bits  (00:19)

The flags live in the application program status register, APSR, which is the top part of xPSR. N is bit 31, Z is bit 30, C is bit 29, V is bit 28, and Q is bit 27.

### The S suffix  (00:35)

On the Cortex-M3, an instruction changes the flags only when we ask for it, with the S suffix. ADD R0, R1, R2 leaves the flags alone, but ADDS R0, R1, R2 updates them. The compare instructions, CMP, CMN, TST and TEQ, always update the flags, because that is their only job.

### 32 bits: unsigned and signed  (00:57)

A 32-bit register can hold two kinds of numbers. As unsigned numbers, it goes from 0 to 0xFFFFFFFF, which is 4,294,967,295. As signed numbers in two's complement, it goes from 0x80000000, which is minus 2,147,483,648, up to 0x7FFFFFFF, which is plus 2,147,483,647. C watches the unsigned edge, where 0xFFFFFFFF wraps around to 0. And V watches the signed edge, where 0x7FFFFFFF wraps around to 0x80000000.

### N: negative  (01:48)

N, the negative flag, is simply a copy of bit 31 of the result. In two's complement, bit 31 is the sign bit. So N is 1 when the result, read as a signed number, is negative. It is the sign flag of other processors, like the 8086, with a new name.

### Z: zero  (02:07)

Z, the zero flag, is 1 when all 32 bits of the result are zero. In every other case, Z is 0.

### C: carry

C, the carry flag, means different things for different instructions. In an addition, C is the carry out of bit 31, so it shows an unsigned overflow. In a subtraction, C is 1 when there is no borrow. And in a shift, C gets the last bit that was shifted out.

### V: overflow  (02:33)

V, the overflow flag, shows a signed overflow: the true result does not fit into 32 bits as a signed number. In an addition, this happens when two numbers with the same sign give a result with the other sign. In hardware, V is the carry into bit 31, exclusive-ORed with the carry out of bit 31.

### Case 1: 5 + 3  (02:54)

Now the cases, starting with addition. Case one: 5 plus 3. The result is 8. Bit 31 is 0, so N is 0. The result is not zero, so Z is 0. There is no carry out of bit 31, so C is 0. And two positive numbers gave a positive result, so V is 0.

### Case 2: 0x7FFFFFFF + 1  (03:17)

Case two: 0x7FFFFFFF plus 1. The result is 0x80000000. Bit 31 is now 1, so N is 1. There is no carry out, so C is 0. But the largest positive number plus 1 gave a negative result, so V is 1. This is a signed overflow. Read as unsigned numbers, the answer is still correct.

### Case 3: 0xFFFFFFFF + 1  (03:43)

Case three: 0xFFFFFFFF plus 1. All 32 bits become 0, and a carry comes out of bit 31. So Z is 1, C is 1, and N is 0. As signed numbers, this is minus 1 plus 1, which is 0, so V is 0. Here the unsigned result overflowed, but the signed one did not.

### Case 4: 0x80000000 + 0x80000000  (04:05)

Case four: 0x80000000 plus 0x80000000. The result is 0, with a carry out. So Z is 1 and C is 1. And two negative numbers gave 0, which is not negative, so V is 1 as well. Now both the unsigned and the signed results are wrong.

### Carry and overflow are independent  (04:27)

So carry and overflow are independent. C tells us about unsigned numbers, and V about signed numbers. The processor does not know which kind we mean, so it sets both, and our program looks at the right one.

| case | addition | result | C | V |
|---|---|---|---|---|
| 1 | 5 + 3 | 0x00000008 | 0 | 0 |
| 2 | 0x7FFFFFFF + 1 | 0x80000000 | 0 | 1 |
| 3 | 0xFFFFFFFF + 1 | 0x00000000 | 1 | 0 |
| 4 | 0x80000000 + 0x80000000 | 0x00000000 | 1 | 1 |

### Subtraction: cases 5 and 6  (04:41)

Now subtraction. Inside the processor, a minus b is calculated as a plus NOT b plus 1. That is why C is 1 when there is no borrow. Case five: 5 minus 3 gives 2, and C is 1. Case six: 3 minus 5 gives 0xFFFFFFFE, which is minus 2. Now there is a borrow, so C is 0, and N is 1.

### Careful: the opposite of Intel  (05:07)

Be careful here. This is the opposite of Intel processors, like the 8085, the 8086 and today's x86 PCs, where the carry flag is 1 when there is a borrow. On ARM, after a subtraction, C equal to 1 means no borrow.

| after a subtraction | borrow | no borrow |
|---|---|---|
| 8085, 8086, x86 | CY = 1 | CY = 0 |
| ARM (Cortex-M3) | C = 0 | C = 1 |

### Cases 7 and 8  (05:24)

Case seven: 5 minus 5 gives 0, so Z is 1, and C is 1, because there is no borrow. Case eight: 0x80000000 minus 1. The most negative number minus 1 gives 0x7FFFFFFF, a positive number. So V is 1, a signed overflow, and C is 1.

### Exactly when V and C are set  (05:46)

So when exactly does V become 1? In an addition, only when both numbers have the same sign, and the result has the other sign. In a subtraction, only when the two numbers have different signs, and the result does not have the sign of the first number. And C? In an addition, C is 1 when the unsigned sum is bigger than 0xFFFFFFFF. In a subtraction, C is 0 when the second number is bigger than the first, as unsigned numbers.

| flag | only when |
|---|---|
| V = 1 in ADD | (+) + (+) = (−)    or    (−) + (−) = (+) |
| V = 1 in SUB | (+) − (−) = (−)    or    (−) − (+) = (+) |
| C = 1 in ADD | unsigned sum  >  0xFFFFFFFF |
| C = 0 in SUB | second number  >  first  (unsigned): borrow |

### Why we need both C and V  (06:15)

This is why we need both C and V. Take CMP R0, R1, with R0 equal to 0xFFFFFFFF and R1 equal to 1. CMP subtracts, and only sets the flags: N is 1, Z is 0, C is 1, and V is 0. As unsigned numbers, R0 is bigger, and BHI, which needs C equal to 1 and Z equal to 0, jumps. As signed numbers, R0 is minus 1, which is smaller, and BLT, which needs N not equal to V, jumps.

### Condition codes  (06:51)

Here are the conditions that test the flags. EQ and NE test Z. CS and CC test C, and they are also called HS and LO, for unsigned higher-or-same and lower. MI and PL test N, and VS and VC test V. HI and LS are for unsigned comparisons, and GE, LT, GT and LE are for signed comparisons.

| code | meaning | flags |
|---|---|---|
| EQ | equal | Z = 1 |
| NE | not equal | Z = 0 |
| CS / HS | carry / unsigned ≥ | C = 1 |
| CC / LO | no carry / unsigned < | C = 0 |
| MI | negative | N = 1 |
| PL | positive or zero | N = 0 |
| VS | overflow | V = 1 |
| VC | no overflow | V = 0 |

| code | meaning | flags |
|---|---|---|
| HI | unsigned > | C = 1 and Z = 0 |
| LS | unsigned ≤ | C = 0 or Z = 1 |
| GE | signed ≥ | N = V |
| LT | signed < | N ≠ V |
| GT | signed > | Z = 0 and N = V |
| LE | signed ≤ | Z = 1 or N ≠ V |

### Logical and shift instructions  (07:19)

Logical instructions with S, like ANDS, ORRS and MOVS, update N and Z, and they do not change V. TST is an AND that only sets the flags: TST R0, #1 makes Z equal to 1 when bit 0 of R0 is 0. And in a shift, C gets the bit that falls out. With R0 equal to 0x80000001, LSLS R0, R0, #1 gives 0x00000002, and C is 1.

### Q: saturation  (07:51)

The fifth flag, Q, is the saturation flag. SSAT R0, #8, R1 limits R1 to the signed 8-bit range, from minus 128 to 127. If R1 is 300, R0 becomes 127, and Q is set to 1. Q is sticky: it stays 1 until the program clears it, by writing to APSR with MSR.

### No parity, no auxiliary carry  (08:14)

Notice what is missing. The Cortex-M3 has no parity flag, and no auxiliary carry flag, which Intel processors like the 8086 have. If a program needs the parity of a value, it calculates it in software. To read the flags, we use MRS R0, APSR, or the CMSIS function __get_APSR in C.

### Practice  (08:38)

Now try this yourself. Pause the video. ADDS R0, R1, R2, with R1 and R2 both equal to 0x40000000. What are N, Z, C and V? The answer: the result is 0x80000000, so N is 1, Z is 0, C is 0, and V is 1, because two positive numbers gave a negative result.

### Summary  (09:05)

Here is the summary. N is the sign of the result, and Z shows a zero result. C is the unsigned carry: in subtraction, 1 means no borrow. V is the signed overflow. Q records saturation and stays set. The flags change only with the S suffix or a compare, and the condition codes use C for unsigned and N and V for signed comparisons.

| flag | remember |
|---|---|
| N | sign of the result (bit 31) |
| Z | result is zero |
| C | unsigned carry;  in SUB: 1 = no borrow |
| V | signed overflow |
| Q | saturation, sticky |
| when? | S suffix or CMP / CMN / TST / TEQ |
| branches | unsigned: C (HI, LO);  signed: N and V (GT, LT) |
