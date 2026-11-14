# ar09 · Cortex-M3 Interrupt Handling

What really happens when an interrupt arrives on an ARM Cortex-M3? We see the eight-register stack frame and its layout, why these registers, the vector fetch in parallel, the register updates, the 12-cycle latency, EXC_RETURN and the exception return, and the tricks that make interrupts fast: tail chaining and late arrival. Then nesting, stack usage, and a complete LPC1768 EINT0 walk-through.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Interrupt handling  (00:00)

Today: what really happens when an interrupt arrives in the Cortex-M3. We will see stacking, the vector fetch, and the special return value EXC_RETURN. Then the tricks that make interrupts fast, tail chaining and late arrival, and how interrupts nest.

### Three steps in hardware  (00:18)

When an interrupt is accepted, the processor does three things by itself, in hardware. It saves eight registers on the stack, it fetches the address of the handler from the vector table, and it updates a few registers. Then the handler starts.

### Stacking  (00:33)

First, stacking. The processor pushes R0, R1, R2, R3, R12, LR, the return address, and xPSR onto the current stack. That is eight words, or 32 bytes. This block is called the stack frame.

### The stack frame in memory  (00:50)

In memory, R0 ends up at the lowest address, where SP now points, and xPSR at the highest. For example, if SP was 0x10008000, it becomes 0x10007FE0, 32 bytes lower.

### Why these eight registers  (01:07)

Why only these eight? Because R0 to R3 and R12 are the registers that any C function is allowed to change. So the handler can be a normal C function. If it uses R4 to R11, it saves them itself, like any other function.

### Vector fetch in parallel  (01:25)

At the same time as the stacking, the processor reads the vector of the interrupt from the vector table, over the I-Code bus. The stacking uses a data bus, so both happen in parallel. This is the Harvard architecture at work.

### Register updates  (01:39)

Then a few registers are updated. SP points to the new frame. The PC gets the handler address. IPSR gets the exception number, for example 34 for EINT0. The processor is now in handler mode, using MSP. And LR gets a special value, called EXC_RETURN.

### Latency: 12 cycles  (02:00)

All of this takes only 12 clock cycles, from the interrupt to the first instruction of the handler, when the memory has no wait states. At 100 MHz, that is 120 nanoseconds.

### EXC_RETURN  (02:13)

EXC_RETURN is not a real address. Its upper bits are all ones, and its last hex digit tells the processor how to return. 0xFFFFFFF9 means return to thread mode, using MSP. 0xFFFFFFFD means thread mode, using PSP. And 0xFFFFFFF1 means return to handler mode, to another handler.

| EXC_RETURN | return to | stack |
|---|---|---|
| 0xFFFFFFF9 | thread mode | MSP |
| 0xFFFFFFFD | thread mode | PSP |
| 0xFFFFFFF1 | handler mode | MSP |

### Returning: unstacking  (02:39)

At the end, the handler returns with BX LR, like a normal function. But when the processor sees an EXC_RETURN value going into the PC, it starts the exception return: it pops the eight registers back, which is called unstacking, and the program continues exactly where it was interrupted.

### Two interrupts: A and B  (02:58)

Now the clever tricks. Suppose two interrupts come together, A and B, and B has to wait for A. Without any trick, the processor would unstack after A, and then stack the same registers again for B. That is wasted work.

### Tail chaining  (03:13)

The Cortex-M3 does tail chaining instead. When A ends and B is pending, it skips the unstacking and the stacking, and jumps straight to handler B. This takes only 6 cycles, instead of about 24.

### Late arrival  (03:27)

Late arrival is the opposite case. A low-priority interrupt starts, and during its stacking, a higher-priority interrupt arrives. The processor keeps the stacking, because the same registers are saved anyway, but fetches the vector of the higher-priority interrupt instead. So the more urgent handler runs first, and the other one follows by tail chaining.

### Nesting  (03:50)

Nesting is when a higher-priority interrupt arrives while a handler is already running. Then the processor stacks a second frame, on top of the first, and runs the new handler. Its LR becomes 0xFFFFFFF1, return to handler mode. When it ends, the first handler continues.

### Stack usage with nesting  (04:10)

Each nesting level needs another 32 bytes of stack, plus what the handler itself uses. So the main stack must be big enough for the deepest nesting that can really happen in our program.

### LPC1768 EINT0 step by step  (04:22)

Let's put it together on the LPC1768. The main loop runs. EINT0 arrives: eight registers are stacked, LR becomes 0xFFFFFFF9, IPSR becomes 34, and the handler toggles the LED. Then BX LR unstacks, and main continues, as if nothing had happened.

### Practice  (04:42)

Now try this yourself. Pause the video. SP is 0x10007000 when an interrupt arrives in thread mode, using MSP. What is SP inside the handler, and what is in LR? The answers: SP is 0x10006FE0, and LR is 0xFFFFFFF9.

### Summary  (05:07)

Here is the summary. On an interrupt, the processor stacks eight registers, fetches the vector in parallel, and puts EXC_RETURN into LR, all in 12 cycles. BX LR with EXC_RETURN unstacks and returns. Tail chaining skips the unstacking and stacking between handlers, late arrival lets an urgent interrupt go first, and nesting stacks a new frame for a higher priority.

|   | remember |
|---|---|
| entry | stack 8 registers + fetch the vector, in parallel |
| registers | SP, PC, IPSR, handler mode;  LR = EXC_RETURN |
| latency | 12 cycles |
| return | BX LR with EXC_RETURN  →  unstacking |
| tail chaining | no unstack / stack between handlers |
| late arrival | an urgent interrupt goes first |
| nesting | a new frame for a higher priority |
