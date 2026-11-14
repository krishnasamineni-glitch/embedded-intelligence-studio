# ar04 · ARM Cortex-M3 Memory Map Explained

How is the 4 GB address space of the ARM Cortex-M3 divided? We go through the fixed regions: code, SRAM, peripheral, external RAM, external device and system, with the private peripheral bus. Then the real memory map of the LPC1768, how a C statement turns into a write to an address, and memory endianness: little endian, big endian, and why it matters.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### The memory map  (00:00)

Today: the memory map of the Cortex-M3, and memory endianness. We will see how the 4 GB address space is divided, where the flash, the RAM and the peripherals of the LPC1768 really are, and in which order the bytes of a word are stored.

### One address space  (00:21)

The Cortex-M3 uses 32-bit addresses, from 0x00000000 to 0xFFFFFFFF, which is 4 GB. Code, data, peripherals and the processor's own system registers all live in this one address space. Even the registers of a peripheral are just addresses: writing to them controls the hardware. This is called memory-mapped I/O.

### The fixed regions  (00:44)

ARM divides the 4 GB into fixed regions, and the division is the same on every Cortex-M3 chip. From the bottom: the code region, the SRAM region and the peripheral region, each 512 MB. Then 1 GB for external RAM and 1 GB for external devices. And at the top, the system region, with the private peripheral bus.

### The code region  (01:07)

The code region starts at address 0. This is where the program lives, usually in flash, together with the vector table. Instructions from this region come in over the I-Code bus, and constants over the D-Code bus.

### SRAM and peripheral regions  (01:21)

The SRAM region, starting at 0x20000000, is meant for data memory. The peripheral region, starting at 0x40000000, holds the peripherals added by the chip vendor. The first megabyte of each of these two regions has a special feature, bit-banding, which lets us change a single bit with one write.

### External RAM and devices  (01:44)

The external RAM and external device regions are for memory and devices connected outside the chip. Many small microcontrollers, like the LPC1768, leave them empty.

### The system region  (01:55)

The system region starts at 0xE0000000. Its first megabyte is the private peripheral bus, with the processor's own blocks: the NVIC at 0xE000E100, SysTick at 0xE000E010, and the system control block. These addresses are the same on every Cortex-M3, so the same CMSIS code works on chips from every vendor.

| private peripheral bus | address |
|---|---|
| NVIC | 0xE000E100 |
| SysTick | 0xE000E010 |
| system control block | 0xE000ED00 |

### The LPC1768 memory map  (02:22)

Now the real map of the LPC1768. The 512 KB flash starts at 0x00000000. 32 KB of local SRAM starts at 0x10000000, still inside the code region. The boot ROM is at 0x1FFF0000.

### More LPC1768 regions  (02:41)

Two more blocks of 16 KB SRAM start at 0x2007C000, in the SRAM region, and the fast GPIO registers start at 0x2009C000. The APB peripherals, like the UARTs, timers and the pin connect block, start at 0x40000000, and the AHB peripherals, like USB and Ethernet, at 0x50000000.

### From C to an address  (03:10)

Let's connect this to our programs. To make pin P0.22 high, we write LPC_GPIO0->FIOSET = 1 << 22. FIOSET of port 0 is at address 0x2009C018, so this line simply writes the value 0x00400000 to that address, and the pin goes high. PINSEL0 is at 0x4002C000, and the NVIC enable register at 0xE000E100.

| register | address | region |
|---|---|---|
| PINSEL0 | 0x4002C000 | APB0 |
| NVIC ISER0 | 0xE000E100 | PPB |

### Endianness  (03:46)

Now endianness. A 32-bit word takes four bytes, at four addresses. But in which order? In little endian, the least significant byte is stored at the lowest address. In big endian, the most significant byte comes first.

### Little and big endian example  (04:02)

For example, store 0x12345678 at address 0x20000000. In little endian, the bytes are 78, 56, 34 and 12. In big endian, they are 12, 34, 56 and 78.

### Cortex-M3 and the LPC1768  (04:20)

The Cortex-M3 can work in either order for data. The chip designer chooses it, and it is fixed when the chip leaves reset. Instruction fetches and the private peripheral bus are always little endian. The LPC1768, like most Cortex-M chips, is little endian.

| access | byte order |
|---|---|
| data | little or big: chosen by the chip designer, fixed at reset |
| instruction fetches | always little endian |
| private peripheral bus | always little endian |
| LPC1768 | little endian |

### Why endianness matters  (04:39)

Why does it matter? When we look at memory byte by byte in the debugger, a word appears reversed. And network protocols send the most significant byte first. The REV instruction reverses the four bytes of a register in one step.

### Summary  (04:54)

Here is the summary. The Cortex-M3 has a 4 GB address space, shared by code, data, peripherals and system registers. The regions are fixed by ARM: code, SRAM, peripheral, external RAM, external device and system. The LPC1768 places its flash at 0, its RAM at 0x10000000 and 0x2007C000, and its peripherals from 0x2009C000, 0x40000000 and 0x50000000. And it stores words in little endian.

|   | remember |
|---|---|
| address space | 4 GB, shared by code, data, peripherals, system |
| regions (ARM) | code · SRAM · peripheral · ext. RAM · ext. device · system |
| LPC1768 | flash 0x0 · RAM 0x10000000, 0x2007C000 · peripherals 0x2009C000, 0x4…, 0x5… |
| byte order | LPC1768: little endian |
