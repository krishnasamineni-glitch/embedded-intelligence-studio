# ar12 · ARM Instruction Set Basics

The basics of the ARM instruction set as used by the Cortex-M3: Thumb-2 with 16-bit and 32-bit instructions, the parts of an instruction (operation, S, condition, destination, operands), the load-store architecture with a worked example, the flexible second operand, narrow and wide encodings, how to load constants with MOVS, MOV, MOVW/MOVT and LDR =, the instruction groups, a complete Keil assembly file, how C passes arguments in R0-R3, and the main assembler directives.

## Files

* [`add3.s`](add3.s) – the complete Keil assembly file of the video: add3 returns R0 + R1 + R2
* [`main_add3.c`](main_add3.c) – calls add3(10, 20, 12) from C: the result is 42

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### ARM instruction set basics  (00:00)

Today: the basics of the ARM instruction set, as used by the Cortex-M3. We will see the Thumb-2 instruction set, the parts of an instruction, the load-store idea, the flexible second operand, how constants get into registers, and the main groups of instructions.

### Thumb-2: 16-bit and 32-bit  (00:19)

The Cortex-M3 runs the Thumb-2 instruction set. It mixes 16-bit and 32-bit instructions in one program. The short ones save memory, and the long ones are more powerful, so we get small code and good speed together. The Cortex-M3 has no separate ARM state: every instruction it runs is a Thumb instruction.

### The parts of an instruction  (00:40)

Every instruction follows the same pattern. Take ADDS R0, R1, #5. ADD is the operation. S means: update the flags. R0 is the destination register, where the result goes. R1 is the first operand, and #5 is the second operand. So R0 becomes R1 plus 5.

### Conditions  (01:04)

An instruction can also carry a condition, written after the operation. BEQ means: branch if equal, that is, only when the Z flag is 1. On the Cortex-M3, branches can be conditional directly, and other instructions become conditional inside an IT block.

### A load-store architecture  (01:22)

ARM is a load-store architecture. Calculations work only on registers, never directly on memory. To change a value in memory, we load it into a register with LDR, calculate, and store it back with STR.

### Example: a counter in memory  (01:36)

For example, a counter at address 0x10000000 holds 41. LDR R1, [R0] loads 41 into R1. ADDS R1, R1, #1 makes it 42. And STR R1, [R0] writes 42 back to memory. Three instructions, and only the first and the last ones touch memory.

### The flexible second operand  (01:57)

The second operand is flexible. It can be an immediate number, like #5, a register, like R2, or a register shifted by the barrel shifter, like R2, LSL #2. So ADD R0, R1, R2, LSL #2 adds R1 and R2 times 4, in one instruction.

### 16-bit or 32-bit encoding  (02:18)

The assembler picks the shortest encoding that works. ADDS R0, R1, R2 fits into 16 bits. ADD R8, R9, R10 needs 32 bits, because most 16-bit instructions can only use the low registers, R0 to R7. We can force the size with the suffixes .N for narrow, and .W for wide.

### Loading a constant  (02:41)

Getting a constant into a register depends on the constant. MOVS R0, #255 is a 16-bit instruction, for the values 0 to 255. A 32-bit MOV can load any 16-bit value, from 0 to 65535, and some special 32-bit patterns, like 0x00FF0000. For any other 32-bit value, we use two instructions.

| instruction | size | constants |
|---|---|---|
| MOVS  R0, #255 | 16-bit | 0 … 255 |
| MOV   R0, #50000 | 32-bit | any 16-bit value: 0 … 65535 |
| MOV   R0, #0x00FF0000 | 32-bit | special 32-bit patterns |
| MOVW + MOVT | 2 × 32-bit | any 32-bit value |

### MOVW, MOVT and LDR =  (03:07)

For example, to load 0x2009C018, the address of FIO0SET: MOVW R0, #0xC018 puts 0xC018 into the lower half, and MOVT R0, #0x2009 puts 0x2009 into the upper half, without touching the lower half. Or we simply write LDR R0, =0x2009C018, and the assembler does the work for us. It stores the constant in memory near the code, and loads it from there.

### The groups of instructions  (03:41)

The instructions fall into a few groups. Data processing: arithmetic, logic, moves, compares, shifts, multiply and divide. Memory access: loads and stores. Branch and control: jumps, function calls and conditional execution. And a few system instructions, like MRS, MSR and WFI.

### A complete Keil assembly file  (04:02)

Here is a complete assembly file for Keil. AREA starts a section of code, THUMB selects Thumb-2, and EXPORT makes the label add3 visible to C. Then come the instructions, and BX LR returns to the caller. END closes the file.

### Calling assembly from C  (04:20)

When C calls add3 with three numbers, they arrive in R0, R1 and R2, and the result goes back in R0. So add3 of 10, 20 and 12 returns 42. This rule, the first four arguments in R0 to R3 and the result in R0, is part of the ARM procedure call standard.

### Useful directives  (04:40)

A few more directives are useful. EQU gives a name to a constant. DCD reserves a 32-bit word with a value, and DCB a byte. SPACE reserves empty bytes. And ALIGN moves to the next word boundary.

| directive | example | meaning |
|---|---|---|
| EQU | LED_BIT   EQU   22 | a name for a constant |
| DCD | table   DCD   1, 2, 3 | 32-bit words with values |
| DCB | msg     DCB   "Hi", 0 | bytes |
| SPACE | buf     SPACE  64 | 64 empty bytes |
| ALIGN | ALIGN | next word boundary |

### Practice  (04:57)

Now try this yourself. Pause the video. Which of these are allowed as one instruction? One: ADD R0, R1, R2, LSL #3. Two: ADD R0, R0, [R1]. Three: MOV R0, #0x12345678. The answers: one is fine. Two is not, because ADD cannot read memory. And three needs two instructions, MOVW and MOVT, or LDR R0, =0x12345678.

### Summary  (05:31)

Here is the summary. The Cortex-M3 runs Thumb-2, with 16-bit and 32-bit instructions. An instruction has an operation, an optional S and condition, a destination and operands. Only loads and stores touch memory. The second operand can be an immediate, a register, or a shifted register. And constants come from MOVS, MOV, MOVW with MOVT, or LDR with an equals sign.

|   | remember |
|---|---|
| Thumb-2 | 16-bit and 32-bit instructions |
| format | operation{S}{cond}  Rd, Rn, operand 2 |
| load-store | only LDR / STR touch memory |
| operand 2 | #immediate,  register,  shifted register |
| constants | MOVS,  MOV,  MOVW + MOVT,  LDR Rd, =value |
