# ar19 · ARM Cortex-M3 System Instructions

The special and system instructions of the ARM Cortex-M3, with 32-bit examples: the special registers and MRS / MSR, reading and writing the flags through APSR, PRIMASK, FAULTMASK and BASEPRI with CPSID and CPSIE (and how BASEPRI works with the 5 priority bits of the LPC1768), CONTROL with MSP and PSP, SVC and a complete SVC handler that finds the SVC number, WFI, WFE, SEV and sleep-on-exit, the barriers DMB, DSB and ISB, atomic updates with LDREX and STREX, and NOP and BKPT. The examples were run in an M-class ARM emulator.

## Files

* [`system_demo.s`](system_demo.s) – MRS / MSR, PRIMASK, BASEPRI, LDREX / STREX and a complete SVC handler

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Special and system instructions  (00:00)

Today: the special and system instructions of the ARM Cortex-M3. These are the instructions that read and write the special registers, switch interrupts off and on, call the operating system, put the processor to sleep, and make memory updates safe. As always, the examples were run in an ARM emulator.

### Special registers: MRS and MSR  (00:22)

Some registers of the Cortex-M3 are not among R0 to R15. The program status register, the three interrupt mask registers PRIMASK, FAULTMASK and BASEPRI, the CONTROL register, and the two stack pointers MSP and PSP are special registers. Normal instructions like MOV cannot reach them. Only two instructions can: MRS reads a special register into a general register, and MSR writes one.

### MRS: read the flags  (00:50)

For example, ADDS adds 1 to 0x7FFFFFFF, so the result is negative and has overflowed. MRS R3, APSR copies the flags into R3, which becomes 0x90000000. Bit 31 is N, and bit 28 is V. This is how a program can save or inspect the flags.

### MSR: write the flags  (01:14)

MSR goes the other way. MSR APSR_nzcvq, R1 copies the top bits of R1 into the flags. With R1 equal to 0x20000000, only the carry flag is set.

### PRIMASK, CPSID and CPSIE  (01:30)

PRIMASK switches off all interrupts that have a configurable priority. CPSID I sets it to 1, so no normal interrupt can run, and CPSIE I clears it again. MRS R5, PRIMASK reads it: 1 after CPSID, and 0 after CPSIE. Keep such sections short, because every interrupt has to wait.

### FAULTMASK and BASEPRI  (01:55)

FAULTMASK, set by CPSID F, blocks even the hard fault, so that only the non-maskable interrupt can run. BASEPRI is more selective: it blocks only the interrupts whose priority number is equal to or higher than its value. The LPC1768 uses 5 priority bits, at the top of each 8-bit priority field. So BASEPRI equal to 0x40 blocks priorities 8 to 31, while the more urgent priorities 0 to 7 still run.

### CONTROL: stack and privilege  (02:27)

The CONTROL register chooses the stack and the privilege level. Bit 1 selects the process stack pointer, PSP, for thread mode, and bit 0 makes thread mode unprivileged. An operating system uses this: tasks run on PSP without privileges, while the kernel and the interrupts use MSP. After writing CONTROL with MSR, an ISB instruction makes sure the next instructions use the new setting.

### SVC: the supervisor call  (02:54)

But how does an unprivileged task ask the kernel for help? With SVC, the supervisor call. SVC #3 raises the SVC exception on purpose, and its handler runs in privileged handler mode. The handler finds the number 3 in the instruction itself: it takes the stacked return address from the exception frame, and reads the byte just before it.

### Finding the SVC number  (03:17)

Here is the complete handler. TST LR, #4 checks EXC_RETURN to find which stack holds the frame, MRS reads that stack pointer, and the stacked PC sits 24 bytes above it. LDRB R0, [R1, #-2] then fetches the SVC number.

### Sleeping: WFI, WFE, SEV  (03:34)

To save power, WFI, wait for interrupt, stops the processor clock until an interrupt arrives. WFE, wait for event, is similar, but it also wakes up on an event, and returns at once if an event happened earlier. SEV sends such an event, which is useful when several processors share data. And with the SLEEPONEXIT bit set, the processor goes back to sleep by itself after every interrupt handler.

### Barriers: DMB, DSB, ISB  (04:00)

The barrier instructions control the order of memory accesses. DMB, data memory barrier, makes sure that the memory accesses before it are seen before those after it. DSB, data synchronization barrier, waits until all earlier memory accesses are complete. And ISB, instruction synchronization barrier, flushes the pipeline, so the following instructions are fetched again, for example after changing the CONTROL register.

### LDREX and STREX  (04:26)

LDREX and STREX make a read, modify, write sequence safe, without switching interrupts off. LDREX reads the word and marks the address for exclusive access. STREX stores the new value only if that exclusive access is still intact, for example if no interrupt came in between, and its status register gets 0 for success or 1 for failure. If it fails, the loop simply tries again. Starting from 41, the loop ends with 42 in memory and 0 in R2.

### NOP and BKPT  (04:59)

Two small ones to finish. NOP does nothing, and is used for padding and alignment. BKPT stops the processor and hands control to the debugger, like a breakpoint written into the program.

### Practice  (05:12)

Now try this yourself. Pause the video. After CMP R0, R0, what does MRS R4, APSR give? The answer: 0x60000000. A value compared with itself gives zero with no borrow, so Z and C, bits 30 and 29, are set.

### Summary  (05:33)

Here is the summary. MRS and MSR are the only way to the special registers. CPSID, CPSIE, PRIMASK, FAULTMASK and BASEPRI control the interrupts, and CONTROL chooses the stack and the privilege. SVC calls the system, WFI and WFE save power, the barriers keep memory accesses in order, and LDREX and STREX make updates atomic.

|   | remember |
|---|---|
| MRS  MSR | the only way to the special registers |
| CPSID  CPSIE | PRIMASK, FAULTMASK: interrupts off / on |
| BASEPRI | block only the less urgent interrupts |
| CONTROL | stack (MSP / PSP) and privilege |
| SVC | call the system |
| WFI  WFE  SEV | sleep and wake up |
| DMB  DSB  ISB | order of memory accesses, refetch |
| LDREX  STREX | atomic read-modify-write |
