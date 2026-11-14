# ar01 · ARM Processors Explained

Where did ARM come from, and why is it inside almost every phone and microcontroller? We go from Acorn and the first ARM chips, through RISC and the ARM licensing business model, to the classic ARM7TDMI to ARM11 processors, the difference between an architecture and a processor, and the three Cortex profiles: Cortex-A for applications, Cortex-R for real-time systems and Cortex-M for microcontrollers. Finally we see where the LPC1768, a popular Cortex-M3 microcontroller, fits in.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### ARM microprocessors  (00:00)

Today: ARM microprocessors. We will see where ARM came from, how ARM works as a company, the classic ARM processors, and the three Cortex families, A, R and M, and how they compare. And we will see where the LPC1768, a popular Cortex-M3 microcontroller, fits in.

### ARM is everywhere  (00:20)

ARM processors are everywhere. Almost every smartphone and tablet has one. So do smart watches, cars, routers, hard disks, washing machines, toys and smart cards. Most of them are tiny ARM cores hidden inside a bigger chip.

### Acorn, 1983  (00:37)

The story begins in 1983 in Cambridge, England, at a company called Acorn Computers. Acorn wanted a faster processor for its next computer, but nothing on the market fitted. So a small team, led by Sophie Wilson and Steve Furber, designed their own: the Acorn RISC Machine, or ARM.

### ARM1 and ARM2  (00:57)

The first chip, ARM1, came back from the factory in 1985, and it worked the first time. It had only about 25,000 transistors. In 1987, the ARM2 powered Acorn's Archimedes computer.

### RISC  (01:13)

Why was it so small? Because ARM is a RISC design: a reduced instruction set computer. The instructions are simple and of fixed length, only load and store instructions touch memory, there are many registers, and the work is pipelined. Small chips use little power, and that later made ARM perfect for battery-powered devices.

### 1990: the ARM company  (01:33)

In 1990, Acorn, Apple and VLSI Technology founded a new company for the processor: Advanced RISC Machines Limited. Apple needed a low-power processor for its Newton handheld computer. Since then, ARM stands for Advanced RISC Machines.

### The licensing business model  (01:49)

ARM does something unusual: it does not make chips. It designs processor cores and sells licences. A partner company, like NXP, ST or Texas Instruments, puts the ARM core into its own chip, adds memory and peripherals, and pays ARM a royalty for every chip sold. That is why the LPC1768 is made by NXP, but has an ARM core inside.

### ARM7TDMI to ARM11  (02:12)

The first big success was the ARM7TDMI, in 1994. T means Thumb, a set of 16-bit instructions for smaller code. D means debug support, M an enhanced multiplier, and I the EmbeddedICE debug logic. It went into mobile phones, the Game Boy Advance and the first iPods. Then came ARM9 and ARM11, and the ARM11 was inside the first iPhone.

### Architecture vs processor  (02:38)

Two words are easy to mix up. The architecture is the instruction set and the programmer's view: ARMv4, v5, v6, v7, v8. A processor is one design that implements it. The ARM7TDMI implements ARMv4T, and the Cortex-M3 implements ARMv7-M.

### The Cortex profiles  (02:58)

With ARMv7, ARM split its processors into three profiles, each for a different job, under a new name: Cortex. A for applications, R for real-time, and M for microcontrollers. The very first Cortex processor, in 2004, was the Cortex-M3.

### Cortex-A  (03:17)

Cortex-A processors run full operating systems like Linux and Android. They have a memory management unit for virtual memory, run at the highest clock speeds, and often come with several cores. You find them in phones, tablets, smart TVs and the Raspberry Pi.

### Cortex-R  (03:34)

Cortex-R processors are built for real-time work, where the answer must come within a fixed, short time, every time. They are used in hard disk and SSD controllers, in car braking and airbag systems, and in mobile modems. Some run two cores in lock-step, which check each other for safety.

### Cortex-M  (03:54)

Cortex-M processors are made for microcontrollers: low cost, low power, and easy to program in C. They have a fixed memory map and a built-in interrupt controller, the NVIC, which reacts to interrupts very quickly. The family goes from the tiny Cortex-M0 and M0+, through the M3, the M4 with DSP instructions and an optional floating-point unit, up to the fast M7, and the M23 and M33 with TrustZone security.

### Comparison  (04:25)

Let's compare the three. Cortex-A is for rich operating systems, with an MMU and the highest speed. Cortex-R is for hard real-time tasks, fast and predictable. Cortex-M is for microcontrollers, with the lowest cost and power, and the simplest programming. A and R can run both ARM and Thumb instructions, while Cortex-M runs only Thumb-2.

|   | Cortex-A | Cortex-R | Cortex-M |
|---|---|---|---|
| used for | rich operating systems | hard real-time tasks | microcontrollers |
| memory | MMU (virtual memory) | MPU, fast local memory | fixed map, optional MPU |
| speed | highest | high, predictable | low to medium |
| cost / power | highest | medium | lowest |
| instructions | ARM + Thumb | ARM + Thumb | Thumb-2 only |
| examples | phones, Raspberry Pi | disk drives, brakes | LPC1768, appliances |

### The LPC1768  (04:49)

And the LPC1768? It is a microcontroller from NXP, built around an ARM Cortex-M3 core running at up to 100 MHz. NXP added 512 KB of flash, 64 KB of RAM, and peripherals like GPIO, UART, SPI, I2C, ADC, USB, CAN and Ethernet. The core is ARM's, and everything around it is NXP's.

### Summary  (05:18)

Here is the summary. ARM began at Acorn in 1983, and became a company in 1990. ARM licenses its designs, and partners build the chips. The Cortex processors come in three profiles: A for applications, R for real-time, and M for microcontrollers. And the LPC1768 is a Cortex-M3.

|   | remember |
|---|---|
| 1983 / 1990 | ARM begins at Acorn / ARM Ltd is founded |
| business | ARM licenses designs, partners build chips |
| Cortex profiles | A = applications,  R = real-time,  M = microcontrollers |
| LPC1768 | an NXP chip with a Cortex-M3 core |
