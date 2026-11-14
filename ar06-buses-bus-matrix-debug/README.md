# ar06 · ARM Cortex-M3 Buses, Bus Matrix and Debug System Explained

Which bus carries each access in an ARM Cortex-M3? We see the four bus interfaces (I-Code, D-Code, system and PPB), how the address decides the bus, the bus matrix with arbitration, unaligned access, bit-band and the write buffer, and the multilayer AHB matrix of the LPC1768. Then the debug system: debug probe, JTAG and SWD, the debug access port, FPB breakpoints, DWT watchpoints and trace with ITM, ETM, TPIU and SWO.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Buses and debug  (00:00)

Today: the bus system of the Cortex-M3, the bus matrix, and the debug system. We will see which bus carries each access, what the bus matrix does, and how a debugger can stop the processor, look inside it, and trace what it does.

### Four bus interfaces  (00:17)

A processor needs buses to fetch instructions, to read and write data, and to reach its own system blocks. The Cortex-M3 has four bus interfaces: I-Code, D-Code, the system bus, and the private peripheral bus, or PPB. I-Code, D-Code and the system bus are AHB-Lite buses, from the AMBA bus standard of ARM.

### I-Code and D-Code  (00:38)

The I-Code bus fetches instructions from the code region, from 0x00000000 to 0x1FFFFFFF. The D-Code bus carries data accesses to the same region, like reading a constant table stored in flash. Because the two buses are separate, an instruction fetch and a data read can happen at the same time. This is a Harvard bus architecture, even though there is only one address space.

### The system bus  (01:03)

The system bus carries all accesses from 0x20000000 to 0xDFFFFFFF: the SRAM, the peripherals, and external memory and devices. Instructions can be fetched over the system bus too, so a program can run from SRAM. But for the best speed, program code is kept in the code region.

### The PPB  (01:25)

The private peripheral bus, at 0xE0000000, reaches the processor's own system blocks: the NVIC, SysTick, the system control block, and the debug units. Its external part is an APB bus, a simpler and slower bus, used for blocks like the trace port interface unit.

### The address decides the bus  (01:46)

So the address decides the bus. Fetching an instruction at 0x00000400 uses I-Code. Reading a constant at 0x00002000 uses D-Code. Writing to the RAM at 0x2007C000, or to UART0 at 0x4000C000, uses the system bus. And enabling an interrupt at 0xE000E100 uses the private peripheral bus.

### The bus matrix and arbitration  (02:16)

All these buses meet in the bus matrix. It connects the processor, and also the debugger, to the bus interfaces. When the processor and the debugger want the same bus at the same moment, the bus matrix decides who goes first. This is called arbitration.

### Three more jobs of the bus matrix  (02:31)

The bus matrix has three more jobs. First, it splits an unaligned access into aligned transfers. Second, it turns a write to a bit-band alias address into a read-modify-write of the real bit. And third, it has a write buffer: the processor can go on to the next instruction while a write is still finishing.

### LPC1768 multilayer AHB matrix  (02:53)

Outside the processor, the chip vendor adds its own buses. On the LPC1768, the three AHB-Lite buses of the core connect to a multilayer AHB matrix. The DMA controller, USB and Ethernet are bus masters on it too. So the core can fetch from flash while the DMA moves data into RAM, at the same time. Slower peripherals sit on two APB buses, behind AHB-to-APB bridges.

### The debug system  (03:23)

Now the debug system. The debugger software on the PC talks to a small debug probe over USB, and the probe connects to the debug pins of the chip. With it, we can halt the processor, run one instruction at a time, read and change registers and memory, and set breakpoints.

### JTAG and SWD  (03:41)

There are two ways to connect. JTAG uses four pins, TCK, TMS, TDI and TDO, and an optional reset pin. Serial Wire Debug, or SWD, needs only two pins: SWCLK for the clock, and SWDIO for the data. On the LPC1768, the SWD pins share the JTAG pins TCK and TMS, so one debug connector works both ways.

### The debug access port  (04:10)

Inside the chip, the pins go to the debug access port, or DAP. The DAP is connected to the bus matrix, so the debugger can read memory and peripheral registers even while the program is running, without stopping the processor. It also reaches the debug registers, to halt, step and run the core.

### Breakpoints: the FPB  (04:30)

Breakpoints come from the Flash Patch and Breakpoint unit, FPB. It compares every instruction fetch with up to six addresses, so the core stops at code in flash without changing the flash. For code in RAM, the debugger can also insert the BKPT instruction.

### Watchpoints: the DWT  (04:47)

Watchpoints come from the Data Watchpoint and Trace unit, DWT. It has four comparators, and can stop the core when a chosen variable is read or written. This is how we find the line of code that changes a variable unexpectedly.

### Trace  (05:01)

Trace shows what the program does, without stopping it. The DWT has a cycle counter, and can sample the program counter. The ITM, the instrumentation trace macrocell, sends printf-like messages from our code. The ETM, the embedded trace macrocell, records the executed instructions, if the chip has it. And the TPIU sends all this out of the chip, for example through the single SWO pin.

### Practice  (05:29)

Now try this yourself. Pause the video. Which bus carries each access? One: fetching an instruction at 0x00000100. Two: reading UART0 at 0x4000C000. Three: writing SysTick at 0xE000E010. The answers are: I-Code, the system bus, and the private peripheral bus.

### Summary  (05:54)

Here is the summary. The Cortex-M3 has four buses: I-Code and D-Code for the code region, the system bus for SRAM, peripherals and external memory, and the private peripheral bus for the system region. The bus matrix connects them, arbitrates, handles unaligned and bit-band accesses, and buffers writes. And through JTAG or SWD, the debug units let us halt, step, set breakpoints and watchpoints, and trace.

|   | remember |
|---|---|
| I-Code, D-Code | the code region (flash): instructions, constants |
| system bus | SRAM, peripherals, external memory |
| PPB | the system region: NVIC, SysTick, SCB, debug |
| bus matrix | arbitration, unaligned, bit-band, write buffer |
| debug | JTAG / SWD, DAP, FPB breakpoints, DWT watchpoints |
| trace | DWT, ITM, ETM  →  TPIU  →  SWO |
