# ar14 · ARM Logic and Bit Manipulation

Every logic and bit manipulation instruction of the ARM Cortex-M3, bit by bit on 32-bit values: AND as a mask, ORR to set bits, BIC to clear bits, EOR to toggle bits, ORN, how to set, clear and toggle one bit of a hardware register, TST, TEQ, CMP and CMN, the bit field instructions UBFX, SBFX, BFI and BFC, and CLZ, RBIT, REV and REV16. Every value was checked in an ARM emulator.

## Files

* [`logic_demo.s`](logic_demo.s) – every logic and bit-manipulation example of the video, bit by bit on 32-bit values

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Logic and bit manipulation  (00:00)

Today: the logic and bit manipulation instructions of the ARM Cortex-M3. We will see AND, OR, exclusive OR and bit clear, how to set, clear and toggle a single bit, the test and compare instructions, and the powerful bit field instructions, all with 32-bit examples.

### Bit by bit, all 32 bits  (00:20)

Logic instructions work bit by bit, on all 32 bits at the same time. Our example value is 0x12345678 in R0.

### AND: keep only some bits  (00:30)

AND keeps a bit only where both operands have a 1. So AND R1, R0, #0xFF keeps the lowest byte and clears the rest: the result is 0x00000078. The second operand works like a mask.

### ORR: set bits  (00:44)

ORR sets bits. ORR R1, R0, #0x80000000 sets bit 31, and gives 0x92345678. Every bit that is 1 in the mask becomes 1, and the other bits stay as they were.

### BIC clears, EOR toggles  (01:02)

BIC, bit clear, clears bits. BIC R1, R0, #0xF0 clears bits 7 to 4, and gives 0x12345608. EOR, exclusive OR, toggles bits. EOR R1, R0, #0xFF inverts the lowest byte, and gives 0x12345687.

### Set, clear and toggle one bit  (01:26)

These three are exactly what we need for hardware registers. ORR with 1 shifted left by 22 sets bit 22, BIC with the same mask clears it, and EOR toggles it. All the other bits stay untouched. ORN, OR NOT, is a fourth one: it ORs with the inverted operand.

### TST: test bits  (01:46)

TST tests bits. It does an AND, but keeps only the flags. TST R0, #0x80 gives Z equal to 1, because bit 7 of R0 is 0. And TST R0, #0x40 gives Z equal to 0, because bit 6 is 1.

### TEQ, CMP and CMN  (02:07)

TEQ does an exclusive OR and keeps only the flags, so Z is 1 when the two values are equal. CMP subtracts, as we saw before, and CMN, compare negative, adds. With R4 equal to 5 and R3 equal to minus 5, CMN R4, R3 gives 0, so Z is 1.

### UBFX: extract a bit field  (02:27)

Now the bit field instructions. UBFX, unsigned bit field extract, takes a group of bits and moves it down to bit 0. UBFX R1, R0, #8, #4 takes 4 bits, starting at bit 8, so bits 11 to 8 of 0x12345678, and gives 6.

### SBFX: signed bit field  (02:49)

SBFX does the same, but treats the field as a signed number. The 4-bit field 1111 becomes minus 1, which is 0xFFFFFFFF.

### BFI and BFC  (03:00)

BFI, bit field insert, does the opposite of extract. BFI R1, R2, #8, #4 copies the lowest 4 bits of R2 into bits 11 to 8 of R1. With R2 equal to 0xA, 0x12345678 becomes 0x12345A78. And BFC, bit field clear, clears a field: BFC R1, #0, #8 gives 0x12345600.

### CLZ, RBIT, REV, REV16  (03:30)

A few more useful ones. CLZ counts the leading zeros: 0x00010000 has 15 zeros above its 1. RBIT reverses the order of all 32 bits, so 1 becomes 0x80000000. REV reverses the four bytes, so 0x12345678 becomes 0x78563412, which converts between little and big endian. And REV16 swaps the bytes in each halfword: 0x34127856.

| instruction | input | result | meaning |
|---|---|---|---|
| CLZ | 0x00010000 | 15 | count leading zeros |
| RBIT | 0x00000001 | 0x80000000 | reverse all 32 bits |
| REV | 0x12345678 | 0x78563412 | reverse the 4 bytes (endianness) |
| REV16 | 0x12345678 | 0x34127856 | swap bytes in each halfword |

### Practice  (04:04)

Now try this yourself. Pause the video. R0 is 0xABCD1234. What do UBFX R1, R0, #16, #8 and BIC R2, R0, #0xFF000000 give? The answers: R1 is 0xCD, and R2 is 0x00CD1234.

### Summary  (04:27)

Here is the summary. AND masks, ORR sets, BIC clears and EOR toggles bits. TST and TEQ test without changing a register, and CMP and CMN compare. UBFX and SBFX extract a bit field, BFI inserts one, and BFC clears one. And CLZ, RBIT and REV count and reverse.

|   | remember |
|---|---|
| AND / ORR / BIC / EOR | mask / set / clear / toggle bits |
| TST / TEQ | test, flags only |
| CMP / CMN | compare by subtracting / adding |
| UBFX / SBFX | extract a bit field (unsigned / signed) |
| BFI / BFC | insert / clear a bit field |
| CLZ / RBIT / REV | count zeros, reverse bits or bytes |
