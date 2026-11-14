# ar11 · ARM Shift and Rotate Instructions

How do shifts and rotates work on an ARM Cortex-M3? With 32-bit examples we see LSL, LSR, ASR, ROR and RRX, what happens to the carry flag, how bits are lost, signed and unsigned division by powers of two, why ASR rounds down, rotate left with ROR, 64-bit shifts with RRX, and the barrel shifter: array indexing and multiplying by constants in one instruction.

## Files

* [`shifts_demo.s`](shifts_demo.s) – every shift, rotate and barrel-shifter example of the video in Cortex-M3 assembly

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Shifts and rotates  (00:00)

Today: the shift and rotate instructions of the Cortex-M3, and the barrel shifter. We will see LSL, LSR, ASR, ROR and RRX with 32-bit examples, and what happens to the carry flag. And we will see how one instruction can shift and add at the same time.

### What a shift does  (00:21)

A shift moves all the bits of a register to the left or to the right. Shifting left by n multiplies by 2 to the power n, and shifting right divides. Shifts are also used to build masks, and to move bit fields into place.

### LSL: logical shift left  (00:38)

LSL, logical shift left, moves every bit to the left. Zeros come in at the right, and the bits that leave at the left are lost. With LSLS, the last bit that leaves goes into the carry flag. For example, 0x0000000F shifted left by 4 gives 0x000000F0: 15 times 16 is 240.

### Shifting left can lose bits  (00:58)

But shifting left can lose bits. 0x40000000 shifted left by 1 gives 0x80000000. As an unsigned number this is still correct, but as a signed number, a positive value became negative. And shifting 0x40000000 left by 2 gives 0: the 1 has gone into the carry flag.

### LSR: logical shift right  (01:22)

LSR, logical shift right, moves every bit to the right, and zeros come in at the left. The last bit that leaves at the right goes into C. 0x000000F0 shifted right by 4 gives 0x0000000F: 240 divided by 16 is 15. So LSR is the unsigned divide by a power of two.

### LSR on a negative number  (01:42)

Now try LSR on a negative number. Minus 8 is 0xFFFFFFF8. Shifted right by 1 with LSR, it becomes 0x7FFFFFFC, a huge positive number. The sign is lost, because a zero came in at the top.

### ASR: arithmetic shift right  (02:00)

ASR, arithmetic shift right, fixes this. It copies the sign bit into the top, so the sign is kept. Minus 8 shifted right by 1 with ASR gives 0xFFFFFFFC, which is minus 4. So ASR is the signed divide by a power of two.

### ASR rounds down  (02:18)

One surprise: ASR always rounds down, towards minus infinity. Minus 7 shifted right by 1 gives minus 4, not minus 3. In C, minus 7 divided by 2 is minus 3, so the compiler adds a small correction for negative numbers before the shift.

### ROR: rotate right  (02:35)

ROR, rotate right, moves the bits to the right, and every bit that leaves at the right comes back in at the left. Nothing is lost. 0x12345678 rotated right by 8 gives 0x78123456. With RORS, C gets the new bit 31.

### Rotate left with ROR  (02:57)

ARM has no rotate left instruction, and it does not need one. Rotating left by n is the same as rotating right by 32 minus n. So rotating 0x12345678 left by 8 is ROR by 24, which gives 0x34567812.

### RRX: rotate through the carry  (03:18)

RRX, rotate right extended, rotates by one bit through the carry flag, like a 33-bit register. The old carry goes into bit 31, and bit 0 goes into the carry. With R0 equal to 3 and C equal to 0, RRXS gives 1, and C becomes 1. Together with LSRS on the upper word, RRX shifts a 64-bit number right by one bit.

### Shift amount in a register  (03:45)

The shift amount can also come from a register. LSL R0, R0, R1 shifts by the number in R1. Only the bottom byte of R1 is used, and for LSL and LSR, a shift by 32 or more gives 0.

### The barrel shifter  (04:01)

Now the best part: the barrel shifter. In ARM, the second operand of many instructions can be shifted on its way into the ALU, in the same instruction. ADD R0, R1, R2, LSL #2 means: R0 equals R1 plus R2 times 4.

### Arrays: start + index x 4  (04:19)

This is perfect for arrays. If R1 holds the start address of an array of 32-bit words, and R2 holds the index, then R1 plus R2 times 4 is the address of that element. LDR R0, [R1, R2, LSL #2] loads it in one instruction. With the array at 0x10000000 and index 3, the address is 0x1000000C.

### Multiply by a constant  (04:47)

It also multiplies by small constants without a multiply instruction. ADD R0, R0, R0, LSL #2 gives R0 plus 4 times R0, which is 5 times R0. And RSB R0, R0, R0, LSL #3 gives 8 times R0 minus R0, which is 7 times R0. With R0 equal to 6, these give 30 and 42.

### Practice  (05:11)

Now try this yourself. Pause the video. R0 is 0xFFFFFFF0, which is minus 16. What do LSR #2 and ASR #2 give? The answers: LSR gives 0x3FFFFFFC, and ASR gives 0xFFFFFFFC, which is minus 4.

### Summary  (05:32)

Here is the summary. LSL multiplies by powers of two, LSR divides unsigned numbers, and ASR divides signed numbers, rounding down. ROR rotates without losing bits, and RRX rotates through the carry. With the S suffix, the last bit shifted out goes into C. And the barrel shifter lets one instruction shift and calculate at the same time.

|   | remember |
|---|---|
| LSL | × 2ⁿ;  zeros in at the right |
| LSR | unsigned ÷ 2ⁿ;  zeros in at the left |
| ASR | signed ÷ 2ⁿ;  sign copied, rounds down |
| ROR | rotate, nothing lost;  rotate left = ROR (32 − n) |
| RRX | rotate one bit through C |
| S suffix | the last bit shifted out  →  C |
| barrel shifter | shift + calculate in one instruction |
