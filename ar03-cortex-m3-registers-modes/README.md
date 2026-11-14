# ar03 · ARM Cortex-M3 Registers and Operating Modes Explained

Every register of the ARM Cortex-M3: the low and high registers, the two stack pointers MSP and PSP, the link register and the program counter, the program status register xPSR with APSR, IPSR and EPSR, the flags, the interrupt masks PRIMASK, FAULTMASK and BASEPRI, and CONTROL. Then the operating modes: thread and handler mode, privileged and unprivileged, and why an operating system needs them.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Registers and modes  (00:00)

Today: the registers of the Cortex-M3, and its operating modes. We will see the sixteen core registers, the special registers, like the program status register and the interrupt masks, and how the processor switches between thread mode and handler mode, and between privileged and unprivileged.

### Overview of the registers  (00:20)

The Cortex-M3 has sixteen core registers, R0 to R15, each 32 bits wide. R0 to R12 are general purpose. R13 is the stack pointer, R14 the link register, and R15 the program counter. Next to them are the special registers: the program status register, three interrupt mask registers, and CONTROL.

### Low and high registers  (00:42)

R0 to R7 are the low registers. Almost every instruction can use them, including the short 16-bit ones. R8 to R12 are the high registers. They are used mainly by 32-bit instructions, and by only a few 16-bit ones, like MOV, ADD and CMP.

### Two stack pointers: MSP and PSP  (01:03)

R13 is the stack pointer, and there are actually two of them. The main stack pointer, MSP, is used after reset and by every exception handler. The process stack pointer, PSP, is used by application tasks when an operating system is running. Only one of them is visible as R13 at a time, and the stack pointer always holds a word-aligned address.

### The link register  (01:26)

R14, the link register, holds the return address of a function. BL, branch with link, jumps to the function and saves the return address in LR. At the end, BX LR jumps back. If BL is at address 0x100, LR becomes 0x105: the address of the next instruction, 0x104, with the lowest bit set to 1, which means Thumb.

### The program counter  (01:51)

R15 is the program counter. It holds the address of the current instruction, and when an instruction reads it, it sees that address plus 4. Writing a new value into the PC makes the processor jump there.

### xPSR  (02:05)

Now the special registers. The program status register, xPSR, is really three registers in one. The application PSR holds the flags in the top bits. The interrupt PSR holds the number of the current exception in the lowest nine bits. And the execution PSR holds the Thumb bit, bit 24.

### The flags  (02:27)

There are five flags. N is set when the result is negative, Z when it is zero, C on a carry, and V on a signed overflow. Q is the saturation flag, which stays set until we clear it. For example, 0x7FFFFFFF plus 1 gives 0x80000000: N is 1, Z is 0, C is 0, and V is 1, because two large positive numbers gave a negative result.

### IPSR and EPSR  (02:54)

IPSR tells which exception is running. In normal code it is 0. Inside the SysTick handler it is 15, and inside the handler of external interrupt 0 on the LPC1768, it is 34. The T bit in EPSR must always be 1, because the Cortex-M3 runs only Thumb code. If it is ever 0, the processor raises a fault.

| running | IPSR |
|---|---|
| normal code (thread mode) | 0 |
| SysTick handler | 15 |
| LPC1768 EINT0 handler | 34  (16 + 18) |

### Interrupt masks  (03:19)

Three registers mask interrupts. When PRIMASK is 1, all interrupts with a programmable priority are blocked. Only NMI and HardFault still get through. FAULTMASK is stronger: it blocks HardFault too, and only NMI remains. BASEPRI blocks only the interrupts whose priority value is equal to or higher than the value in BASEPRI. When BASEPRI is 0, it blocks nothing.

### CONTROL  (03:44)

The CONTROL register has two important bits. Bit 0, nPRIV, selects the privilege of thread mode: 0 is privileged, 1 is unprivileged. Bit 1, SPSEL, selects the stack pointer of thread mode: 0 is MSP, 1 is PSP.

|   | thread mode uses |   |
|---|---|---|
| bit 0  nPRIV | 0 = privileged | 1 = unprivileged |
| bit 1  SPSEL | 0 = MSP | 1 = PSP |

### MRS and MSR  (04:02)

Special registers are not used like R0 to R12. We read them with MRS and write them with MSR, for example MRS R0, CONTROL. In C, CMSIS gives us functions like __get_CONTROL, and __disable_irq, which sets PRIMASK.

### Modes and privilege  (04:20)

Now the operating modes. The Cortex-M3 runs in thread mode while it executes normal code, and in handler mode while it executes an exception or interrupt handler. There are also two privilege levels. Privileged code can do everything. Unprivileged code cannot change CONTROL or the masks, and cannot touch the system control registers. Handler mode is always privileged.

### The mode diagram  (04:45)

After reset, the processor starts in thread mode, privileged, using MSP. An exception switches it to handler mode, and the return brings it back. Privileged thread code can make itself unprivileged by writing CONTROL. But it cannot come back on its own. Only an exception handler can change it back.

### Why: an operating system  (05:05)

Why so many options? For an operating system. The kernel and the handlers run privileged, on the main stack, and the tasks run unprivileged, each on its own process stack, so a faulty task cannot break the whole system. In simple programs without an operating system, everything runs privileged on MSP.

### Summary  (05:26)

Here is the summary. R0 to R12 are general purpose, R13 is the stack pointer, MSP or PSP, R14 the link register, and R15 the program counter. xPSR holds the flags, the exception number and the Thumb bit. PRIMASK, FAULTMASK and BASEPRI mask interrupts, and CONTROL selects privilege and stack. And the processor runs in thread mode or handler mode, privileged or unprivileged.

|   | remember |
|---|---|
| R0 – R12 | general purpose |
| R13 / R14 / R15 | SP (MSP or PSP) / LR / PC |
| xPSR | flags (APSR), exception number (IPSR), Thumb bit (EPSR) |
| masks, CONTROL | PRIMASK, FAULTMASK, BASEPRI;  privilege + stack |
| modes | thread / handler,  privileged / unprivileged |
