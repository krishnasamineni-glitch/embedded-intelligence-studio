# ar18 · C and Assembly Together on ARM Cortex-M3

How C and assembly work together on the ARM Cortex-M3: the ARM procedure call standard (AAPCS), arguments in R0 to R3 and the result in R0, 64-bit results in R1 and R0, the fifth argument on the stack, scratch registers and the saved registers R4 to R11, an 8-byte aligned stack, calling an assembly function from C and a C function from assembly, real compiler output for a C loop, and CMSIS intrinsics such as __disable_irq, __WFI, __CLZ and __REV. The functions were compiled with clang for Cortex-M3 and run in an ARM emulator.

## Files

* [`cabi_demo.s`](cabi_demo.s) – max2, mul64 and sum5 as the compiler makes them, and a caller that passes a fifth argument on the stack
* [`main_cabi.c`](main_cabi.c) – calls the three assembly functions from C

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### C and assembly together  (00:00)

Today: how C and assembly work together on the ARM Cortex-M3. We will see which registers carry the arguments and the result, which registers a function must save, how C calls assembly and assembly calls C, and what the compiler really makes of simple C code.

### One agreement: AAPCS  (00:20)

A C function and an assembly function must agree on where the arguments go, and which registers may change. This agreement is the ARM procedure call standard, AAPCS. Every compiler for ARM follows it, so code from different tools works together.

### Who uses which register  (00:36)

R0 to R3 carry the first four arguments, and R0 carries the result back. R0 to R3 and R12 are scratch registers: a function may change them freely. R4 to R11 must keep their values: if a function uses them, it saves them first and restores them before it returns. SP, LR and PC keep their usual jobs.

### A C function and its assembly  (01:00)

Take a small C function, max2, which returns the larger of two signed numbers. The argument a arrives in R0, and b in R1. The compiler turns it into just four instructions: CMP, an IT block with MOVLE, and BX LR. The result is already in R0, so with minus 5 and 3, max2 returns 3.

### A 64-bit result: R1 and R0  (01:25)

A 64-bit result comes back in two registers: the low word in R0, and the high word in R1. mul64 multiplies two 32-bit numbers into a 64-bit product with a single UMULL. For 0x00010000 times 0x00010000, R0 is 0 and R1 is 1, because the product is 0x0000000100000000.

### The fifth argument on the stack  (01:52)

Only four arguments fit into registers. The fifth one is passed on the stack, at the address in SP when the function starts. So sum5 loads it with LDR R12, [SP], and adds it like the others. sum5 of 1, 2, 3, 4 and 5 returns 15.

### Calling assembly from C  (02:10)

To call our own assembly function from C, we export its label in the assembly file, and declare a matching prototype in C. Then C calls it like any other function, and the linker connects the two. The assembly code only has to follow the standard: arguments in R0 to R3, the result in R0, and BX LR to return.

### Saving R4 to R11, an aligned stack  (02:32)

If an assembly function needs more registers, it can use R4 to R11, but it must save them. PUSH {R4-R6, LR} at the start and POP {R4-R6, PC} at the end do both jobs: they keep the caller's values, and they return. Push an even number of registers, so that the stack stays aligned to 8 bytes, as the standard requires at every call.

### Calling C from assembly  (02:56)

Assembly can call C functions too, with BL. But after the call, R0 to R3 and R12 may hold anything, because the C function is allowed to change them. So values that must survive the call are kept in R4 to R11. And the C function's result is waiting in R0.

### What the compiler makes of a loop  (03:16)

Here is what the compiler makes of a C loop that adds the elements of an array. LDR R3, [R2], #4, then SUBS and BNE: exactly the pattern we write by hand. Reading the compiler's output is a great way to learn assembly, and to check that your C code is efficient.

### CMSIS intrinsics  (03:35)

Some instructions have no operator in C. CMSIS provides them as intrinsic functions, and each one compiles into a single instruction. __disable_irq and __enable_irq become CPSID I and CPSIE I, __WFI becomes WFI, and __CLZ, __REV and __RBIT become the instructions of the same names. This is the easiest and most portable way to use them from C.

| in C | instruction |
|---|---|
| __disable_irq() | CPSID  I |
| __enable_irq() | CPSIE  I |
| __WFI() | WFI |
| __CLZ(x) | CLZ |
| __REV(x) | REV |
| __RBIT(x) | RBIT |
| __DSB()  __ISB() | DSB  ISB |

### When to write assembly  (04:03)

Today most code is written in C, because compilers are very good. Assembly is still the right tool for startup code, for some exception details, for very tight loops, and above all for understanding what the processor really does. The calling standard lets the two work together safely.

### Practice  (04:20)

Now try this yourself. Pause the video. A function is called as f of 10, 20, 30, 40, 50 and 60. Where does each argument arrive? The answers: 10, 20, 30 and 40 in R0 to R3, and 50 and 60 on the stack, at SP and at SP plus 4.

### Summary  (04:40)

Here is the summary. R0 to R3 carry the arguments, R0 the result, and R1 too for 64-bit results. Further arguments go on the stack. R0 to R3 and R12 may change in a call, while R4 to R11 must be saved and restored, with an aligned stack. And CMSIS intrinsics give C direct access to special instructions.

|   | remember |
|---|---|
| R0 – R3 | arguments 1 to 4 |
| R0  (R1) | the result  (R1 too for 64 bits) |
| stack | arguments 5, 6, …  at SP, SP + 4, … |
| R0 – R3, R12 | may change in a call |
| R4 – R11 | save and restore;  stack aligned to 8 bytes |
| CMSIS | intrinsics for special instructions |
