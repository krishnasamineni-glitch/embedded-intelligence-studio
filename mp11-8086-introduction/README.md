# mp11 · 8086 Microprocessor Introduction

Meet the 8086, the 16-bit processor after the 8085: its features, an 8085 vs 8086 comparison, the bus interface unit and the execution unit, the 6-byte instruction queue and pipelining, the general purpose registers, memory segments (CS, DS, SS, ES), how the 20-bit physical address is formed (segment x 10H + offset) with two examples, and the nine flags.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.
Signals with a bar on top (R̅D̅) are active low.

### The 8086  (00:00)

Today: the 8086, the 16-bit processor that came after the 8085. We will see its features, its two internal units, the instruction queue, its registers, memory segments, how a physical address is calculated, and its flags.

### 8086 features  (00:18)

Intel released the 8086 in 1978. It is a 16-bit processor: its ALU and registers work on 16 bits, and its data bus is 16 bits wide. It has a 20-bit address bus, so it can address 1 MB of memory. It runs at 5 to 10 MHz, and it comes in a 40-pin package, like the 8085.

### 8085 vs 8086  (00:41)

Let's compare it with the 8085. The data bus grows from 8 to 16 bits. The address bus grows from 16 to 20 bits, so memory grows from 64 KB to 1 MB. The registers become 16 bits. The 8086 can address 64K I/O ports instead of 256. And two new ideas appear: an instruction queue, and memory segmentation.

|   | 8085 | 8086 |
|---|---|---|
| data bus | 8 bits | 16 bits |
| address bus | 16 bits | 20 bits |
| memory | 64 KB | 1 MB |
| registers | 8 bits (pairs: 16) | 16 bits |
| I/O ports | 256 | 64K |
| instruction queue | — | 6 bytes |
| segments | — | CS, DS, SS, ES |

### Two units inside  (01:07)

Inside, the 8086 is divided into two units that work at the same time. The bus interface unit, the BIU, talks to the outside world: it fetches instructions, and reads and writes data. The execution unit, the EU, decodes and executes the instructions.

### Inside the BIU  (01:25)

The BIU contains the four segment registers, CS, DS, SS and ES, and the instruction pointer, IP. An address adder combines a segment and an offset into the 20-bit physical address. And there is a 6-byte instruction queue.

### Inside the EU  (01:42)

The EU contains the ALU, the control unit that decodes instructions, the flag register, and the general purpose registers. These are AX, BX, CX and DX, and the pointer and index registers, SP, BP, SI and DI.

### Pipelining  (01:59)

Here is the trick that makes the 8086 faster. In the 8085, the processor fetches an instruction, executes it, and only then fetches the next one. In the 8086, while the EU is executing, the BIU is already fetching the next bytes into the queue. This overlap is called pipelining. When the EU needs the next instruction, it is usually already waiting in the queue.

### The instruction queue  (02:25)

The BIU fills the queue whenever at least two bytes are free. But after a jump or a call, the bytes in the queue are useless, because the program continues somewhere else. So the queue is cleared, and filling starts again from the new address.

### General purpose registers  (02:41)

Now the registers. AX, BX, CX and DX are 16 bits, and each one can also be used as two 8-bit registers: AX is AH and AL, BX is BH and BL, and so on. AX is the accumulator, BX is often a base address, CX is a counter, and DX holds data and I/O port addresses.

### Memory segments  (03:05)

The 1 MB memory is divided into segments. A segment is a block of up to 64 KB. Four segments can be active at a time: the code segment, CS, for the program; the data segment, DS; the stack segment, SS; and the extra segment, ES.

### Forming the 20-bit address  (03:24)

The registers are only 16 bits, but the address is 20 bits. So how is it formed? The segment register is shifted left by four bits, which is the same as multiplying by 10H, and then the offset is added. For example, with CS equal to 2000H and IP equal to 0050H, the physical address is 20000H plus 0050H, which is 20050H.

### One more example  (03:55)

One more example. DS is 1234H, and the offset is 0022H. Shift 1234H to get 12340H, add 0022H, and the physical address is 12362H. Each segment has its usual partners: CS with IP, SS with SP or BP, DS with BX or SI, and ES with DI.

| segment | offset from |
|---|---|
| CS | IP |
| SS | SP, BP |
| DS | BX, SI |
| ES | DI |

### The 8086 flags  (04:23)

Finally, the flags. The 8086 has a 16-bit flag register with nine flags. Six are status flags, set by the result: carry, parity, auxiliary carry, zero, sign, and the new overflow flag. Three are control flags, set by the program: trap for single stepping, interrupt enable, and direction for string operations.

### Summary  (04:48)

Here is the summary. The 8086 is a 16-bit processor with a 20-bit address bus and 1 MB of memory. The BIU fetches and the EU executes, overlapped with a 6-byte queue. Memory is used in segments, and the physical address is the segment times 10H plus the offset. And it has nine flags.

|   | remember |
|---|---|
| size | 16-bit data,  20-bit address,  1 MB |
| inside | BIU fetches,  EU executes,  6-byte queue |
| memory | segments CS DS SS ES,  segment × 10H + offset |
| flags | 6 status + 3 control |
