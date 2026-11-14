# ar07 · ARM Cortex-M3 Stack and Reset Sequence Explained

How does the ARM Cortex-M3 stack work, and what happens from reset to main()? We see the full descending stack, PUSH and POP step by step with addresses, saving several registers, how functions and nested calls use the stack, local variables and stack overflow. Then the reset sequence: the initial MSP and the reset vector, the Thumb bit, why SP is loaded first, the reset handler, SystemInit, C start-up and the LPC1768 boot loader.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Stack and reset  (00:00)

Today: the stack of the Cortex-M3, and the reset sequence. We will see how PUSH and POP work, how functions use the stack, and every step from reset to main.

### The stack: last in, first out  (00:13)

The stack is an area of RAM used as last in, first out storage. We use it to save registers, to keep return addresses, and for the local variables of functions. The stack pointer, R13, always points to the top of the stack.

### Full descending  (00:28)

The Cortex-M3 stack is full descending. Descending means it grows down, towards lower addresses. Full means the stack pointer points to the last word that was stored, not to the next free one. So the stack starts at the high end of its RAM area, and grows down.

### PUSH  (00:47)

PUSH stores registers on the stack. Suppose SP is 0x10001000, and R0 holds 0x12. PUSH {R0} first subtracts 4 from SP, giving 0x10000FFC, and then stores R0 at that address.

### POP  (01:08)

POP does the opposite. POP {R1} first reads the word at SP into R1, and then adds 4. Now R1 is 0x12, and SP is back at 0x10001000. The data is still in memory, but it is no longer part of the stack.

### Many registers at once  (01:25)

One PUSH can save many registers. PUSH {R4, R5, LR} moves SP down by 12 bytes. The lowest-numbered register always goes to the lowest address: R4 at SP, R5 above it, and LR at the top. POP {R4, R5, PC} reads them back the same way.

### How functions use the stack  (01:46)

This is how functions use the stack. At the start, a function pushes the registers it will change, together with LR. At the end, POP {R4, R5, PC} restores them, and loads the return address straight into the PC. So the function returns in the same instruction.

### Nested calls  (02:05)

With nested calls, every function adds its own frame on top of the stack. main calls f, and f calls g. Each return removes one frame, in the reverse order, so we always get back to the right place.

### Local variables  (02:20)

Local variables live on the stack too. SUB SP, SP, #8 reserves 8 bytes for them, and ADD SP, SP, #8 frees them at the end. In C, the compiler does all of this for us.

### Stack size and overflow  (02:34)

The stack has a fixed size, set in the startup file, for example 0x200, which is 512 bytes. Interrupts also save registers on the stack, automatically. If deep calls or big local arrays need more than that, the stack grows into other data and destroys it. This is a stack overflow, and it causes very strange bugs.

### What happens at reset  (02:55)

Now, what happens at reset? The Cortex-M3 does not simply start running from address 0. First, it reads two words from the start of the vector table.

| address | vector table |
|---|---|
| 0x00000000 | initial MSP value |
| 0x00000004 | reset vector |
| 0x00000008 | NMI |
| 0x0000000C | HardFault |
| ... | more vectors |

### Initial MSP and reset vector  (03:06)

The word at address 0x00000000 is the initial value of the main stack pointer. The word at address 0x00000004 is the reset vector: the address of the reset handler. Then the processor starts executing there, in thread mode, privileged, using MSP.

| address | vector table |
|---|---|
| 0x00000000 | initial MSP value |
| 0x00000004 | reset vector |
| 0x00000008 | NMI |
| 0x0000000C | HardFault |
| ... | more vectors |

### Example on the LPC1768  (03:23)

For example, if the first word is 0x10008000, MSP becomes 0x10008000, the end of the 32 KB local SRAM of the LPC1768. If the second word is 0x00000101, the PC becomes 0x00000100. Bit 0 of the vector is 1 to mark Thumb code, and it is not part of the address.

| address | word |
|---|---|
| 0x00000000 | 0x10008000 |
| 0x00000004 | 0x00000101 |

### Why SP is loaded first  (03:50)

Why is the stack pointer loaded first? Because an NMI or a fault could happen right at the start, and the processor needs a valid stack to handle it. So the stack is ready before the first instruction runs.

### From reset handler to main()  (04:04)

The reset handler comes from the startup file. First it calls SystemInit, which sets up the clock. On the LPC1768, it starts the PLL for a 100 MHz clock. Then the C startup code copies the initial values of global variables from flash to RAM, and clears the other global variables to zero. Finally, it calls main.

### The LPC1768 boot loader  (04:27)

On the LPC1768, a small boot loader in the boot ROM runs before our program. If pin P2.10 is low at reset, it enters ISP mode, so we can program the flash over the serial port. Otherwise, it checks that a valid program is in the flash, and starts it.

### Practice  (04:45)

Now try this yourself. Pause the video. SP is 0x10000800. After PUSH {R0-R3}, what is SP, and where is R2 stored? The answers: SP is 0x100007F0, and R2 is at 0x100007F8.

### Summary  (05:08)

Here is the summary. The Cortex-M3 stack is full descending: PUSH first moves SP down and then stores, and POP first reads and then moves SP up. Functions save LR and the registers they use, and return with POP into the PC. At reset, the processor loads MSP from address 0 and the PC from address 4, and the reset handler sets up the clock and the C variables before main.

|   | remember |
|---|---|
| stack | full descending, in RAM;  SP = R13 |
| PUSH | SP = SP − 4, then store |
| POP | read, then SP = SP + 4 |
| functions | PUSH {..., LR}   ...   POP {..., PC} |
| reset | MSP ← word at 0x0,   PC ← word at 0x4 |
| startup | SystemInit, C variables, then main() |
