# ar15 · ARM Memory Access Instructions

Every way the ARM Cortex-M3 reads and writes memory, with 32-bit examples: LDR and STR, bytes and halfwords with LDRB and LDRH, signed loads with LDRSB and LDRSH, offset, pre-indexed and post-indexed addressing, register offset for arrays, PC-relative loads and the literal pool, LDM and STM, PUSH and POP, a fast block copy, and alignment. Every value was checked in an ARM emulator.

## Files

* [`memory_demo.s`](memory_demo.s) – every load / store example of the video, with the array at 0x2007C000 (LPC1768 AHB SRAM)

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Memory access instructions  (00:00)

Today: the memory access instructions of the ARM Cortex-M3. We will see loads and stores of words, halfwords and bytes, signed loads, all the addressing modes, and how to move many registers in one instruction.

### LDR and STR  (00:15)

LDR loads a word from memory into a register, and STR stores a register into memory. The address always comes from a register, written in square brackets. So LDR R0, [R1] reads the word at the address held in R1.

### Words, halfwords and bytes  (00:32)

LDR and STR move 32-bit words. LDRB and STRB move a single byte, and LDRH and STRH move a halfword, which is 16 bits. When a byte or a halfword is loaded, the upper bits of the register are filled with zeros.

| instruction | size | name |
|---|---|---|
| LDR / STR | 32 bits | word |
| LDRH / STRH | 16 bits | halfword |
| LDRB / STRB | 8 bits | byte |

### Signed loads: LDRSB and LDRSH  (00:52)

For signed numbers, LDRSB and LDRSH fill the upper bits with copies of the sign bit instead. Say the word at 0x2007C010 is 0x1234F680. In little endian, its lowest byte is 0x80. LDRB gives 128, but LDRSB gives minus 128, which is 0xFFFFFF80. In the same way, LDRH gives 0xF680, and LDRSH gives 0xFFFFF680.

| R2 = 0x2007C010 | R0 | value |
|---|---|---|
| LDRB   R0, [R2] | 0x00000080 | 128 |
| LDRSB  R0, [R2] | 0xFFFFFF80 | −128 |
| LDRH   R0, [R2] | 0x0000F680 | 63104 |
| LDRSH  R0, [R2] | 0xFFFFF680 | −2432 |

### Addressing modes: our example  (01:29)

Now the addressing modes. Our example is an array of words at 0x2007C000, holding 0x11111111, 0x22222222, 0x33333333 and 0x44444444, and R1 points to its start.

### Offset addressing  (01:54)

With an offset, LDR R0, [R1, #4] reads from R1 plus 4, so R0 becomes 0x22222222. R1 itself does not change. This is how we reach a field of a structure, or a peripheral register at a fixed distance from its base address.

### Pre-indexed with write-back  (02:12)

With an exclamation mark, LDR R0, [R1, #4]!, the processor first adds 4 to R1, then reads from the new address, and keeps the new value in R1. R0 becomes 0x22222222, and R1 becomes 0x2007C004. This is called pre-indexed addressing, with write-back.

### Post-indexed addressing  (02:38)

Post-indexed addressing does it the other way round. LDR R0, [R1], #4 reads from R1 first, so R0 becomes 0x11111111, and then adds 4 to R1. This is perfect for walking through an array: every load moves the pointer on to the next element.

### Register offset for arrays  (02:58)

The offset can also be a register, even shifted left. LDR R0, [R1, R2, LSL #2] reads element number R2 of a word array that starts at R1. With R2 equal to 3, the address is 0x2007C00C, and R0 becomes 0x44444444.

### PC-relative loads and the literal pool  (03:21)

Constants and addresses are usually loaded relative to the PC. LDR R0, =0x2009C018 becomes a PC-relative load from a literal pool, a small table of constants that the assembler places near the code.

### LDM: load several registers  (03:37)

LDM and STM move several registers in one instruction. LDMIA R0!, {R3-R6} loads four words from the address in R0 into R3, R4, R5 and R6, and then moves R0 on by 16 bytes. IA means increment after.

### The stack: STMDB and LDMIA  (03:59)

STMDB, store multiple, decrement before, is exactly how the stack works. PUSH {R4, LR} is the same as STMDB SP!, {R4, LR}. And POP is LDMIA SP!.

### Copying a block with LDM and STM  (04:17)

Together, LDM and STM copy memory quickly. LDMIA R0!, {R3-R6} followed by STMIA R2!, {R3-R6} copies 16 bytes in just two instructions, and both pointers are ready for the next block.

### Alignment  (04:38)

Words should sit at addresses that are multiples of 4. The Cortex-M3 can load a word from an unaligned address with LDR, but it takes longer. And LDM, STM, LDRD and STRD always need aligned addresses.

### Practice  (04:55)

Now try this yourself. Pause the video. R1 points to our array at 0x2007C000. What are R0 and R1 after LDR R0, [R1, #8]!? The answers: R0 is 0x33333333, and R1 is 0x2007C008, because of the write-back.

### Summary  (05:20)

Here is the summary. LDR and STR move words, with B and H for bytes and halfwords, and SB and SH for signed loads. An offset leaves the base register alone, pre-indexed adds first and writes back, and post-indexed reads first and adds afterwards. A register offset can be shifted, for arrays. And LDM, STM, PUSH and POP move many registers at once.

|   | remember |
|---|---|
| LDR / STR | words;  B, H: bytes, halfwords;  SB, SH: signed |
| [R1, #4] | offset: R1 unchanged |
| [R1, #4]! | pre-indexed: add first, write back |
| [R1], #4 | post-indexed: read first, then add |
| [R1, R2, LSL #2] | register offset, for arrays |
| LDM / STM | many registers;  PUSH / POP |
