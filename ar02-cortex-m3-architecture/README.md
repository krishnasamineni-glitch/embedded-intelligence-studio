# ar02 · ARM Cortex-M3 Architecture Explained

What is inside an ARM Cortex-M3? We go through its main features, the block diagram with the core, NVIC, SysTick, MPU, debug and the bus matrix, the Harvard bus architecture, the three-stage pipeline and what happens on a branch, the data path, and the Thumb-2 instruction set with 16-bit and 32-bit instructions.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Inside the Cortex-M3  (00:00)

Today we open up the ARM Cortex-M3. We will see its main features, its block diagram, its three-stage pipeline, how data flows through it, and its instruction set, Thumb-2.

### Main features  (00:14)

The Cortex-M3 is a 32-bit processor: its registers, its data path and its buses are all 32 bits wide. It implements the ARMv7-M architecture, it can address 4 GB of memory, and it has separate buses for instructions and data.

### The block diagram  (00:32)

Here is the block diagram. In the middle is the processor core. Next to it sits the NVIC, the nested vectored interrupt controller, with the SysTick timer. On the right are the optional memory protection unit and the debug blocks. And at the bottom, the bus matrix connects everything to the outside world.

### The processor core  (00:52)

The core does the actual work. It has a bank of sixteen 32-bit registers, an ALU with a barrel shifter, a single-cycle hardware multiplier and a hardware divider. The fetch unit and the decoder feed it with instructions, and the load-store unit moves data to and from memory.

### NVIC and SysTick  (01:12)

The NVIC is built right into the processor, close to the core. It handles up to 240 interrupts, each with its own priority, and fetches the address of the right interrupt routine automatically. The LPC1768 uses 35 of them. SysTick is a simple 24-bit timer inside the processor, often used for delays and operating system ticks.

### MPU, debug and bus matrix  (01:34)

The memory protection unit can mark regions of memory as read-only, or block a task from touching them. The debug blocks set breakpoints, watch data and send trace information to the debugger. And the bus matrix connects the core to the I-Code, D-Code, system and private peripheral buses.

### Harvard bus architecture  (01:52)

The Cortex-M3 has a Harvard bus architecture. Instructions come in over the I-Code bus, while data travels over the D-Code or the system bus, at the same time. The 8085 had only one bus for both, so it had to take turns.

### The 3-stage pipeline  (02:08)

Instructions go through a three-stage pipeline: fetch, decode and execute. While one instruction executes, the next one is decoded, and the one after that is fetched. So, in the best case, one instruction finishes in every clock cycle.

### Fetching 32 bits, PC + 4  (02:24)

The fetch unit reads 32 bits at a time: two 16-bit instructions, or one 32-bit instruction. Because of the pipeline, when an instruction reads the PC, it sees its own address plus 4.

### Branches and the pipeline  (02:37)

Branches are the weak point of a pipeline. When a branch is taken, the instructions already fetched after it are thrown away, and the pipeline fills up again. That costs extra cycles. The Cortex-M3 reduces this cost by fetching the branch target early, which is called branch speculation.

### The data path  (02:56)

Now the data path. For ADD R0, R1, R2, the two operands are read from the register bank, the second one can pass through the barrel shifter, the ALU adds them, and the result is written back to R0. For a load, LDR R0, [R1, #4], the address R1 plus 4 is calculated first, the load-store unit reads the memory, and the data goes into R0.

### Thumb-2  (03:22)

The instruction set is called Thumb-2. Older ARM processors had two sets: 32-bit ARM instructions, which are powerful but take more memory, and 16-bit Thumb instructions, which are compact but limited. Thumb-2 mixes 16-bit and 32-bit instructions freely, so we get small code and high performance at the same time.

### 16-bit and 32-bit instructions  (03:44)

For example, MOVS R0, #5 is a 16-bit instruction, just 2 bytes. But adding a large constant, like ADD R0, R1, #0x1000, needs a 32-bit instruction, 4 bytes. The assembler chooses the size for us. The Cortex-M3 runs only Thumb-2: it has no ARM state at all.

### More features  (04:09)

A few more features make the Cortex-M3 easy to use: hardware divide instructions, SDIV and UDIV, bit-field instructions, support for unaligned data, bit-banding, and low-power sleep modes entered with WFI.

### The LPC1768  (04:25)

In the LPC1768, the core runs at up to 100 MHz, so one clock cycle lasts 10 nanoseconds. With the pipeline, that is up to 100 million instructions per second in the best case. Around the processor, NXP adds the flash, the RAM, its own bus matrix and the peripherals.

### Summary  (04:44)

Here is the summary. The Cortex-M3 is a 32-bit ARMv7-M processor with Harvard buses. Its main blocks are the core, the NVIC with SysTick, the MPU, the debug blocks and the bus matrix. It has a three-stage pipeline, and it runs the Thumb-2 instruction set of 16-bit and 32-bit instructions.

|   | remember |
|---|---|
| type | 32-bit, ARMv7-M, Harvard buses |
| blocks | core, NVIC + SysTick, MPU, debug, bus matrix |
| pipeline | fetch, decode, execute |
| instructions | Thumb-2: 16-bit and 32-bit mixed |
