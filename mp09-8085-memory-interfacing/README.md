# mp09 · 8085 Memory Interfacing Explained

How do you connect ROM and RAM chips to the 8085 so that every address reaches exactly one location? The pins of a memory chip, how many address lines a chip needs, the latched buses, MEMR and MEMW from IO/M, RD and WR, the idea of address decoding, the 74LS138 decoder, the complete circuit for an 8K EPROM and an 8K RAM, checking one address, address ranges, the memory map, and absolute vs partial decoding.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.
Signals with a bar on top (R̅D̅) are active low.

### Memory interfacing  (00:00)

Today: memory interfacing. How do we connect ROM and RAM chips to the 8085, so that every address reaches exactly one memory location? We will connect an 8K EPROM and an 8K RAM, using a 74LS138 decoder.

### A memory chip  (00:18)

First, the memory chip itself. A chip like the 6264 is an 8K by 8 RAM. It has address lines, A0 to A12, to pick one location inside the chip. It has eight data lines, D0 to D7. And it has control inputs: CS selects the chip, OE enables reading, and WE enables writing. All three are active low. An EPROM like the 2764 is the same, but without WE.

### How many address lines?  (00:49)

How many address lines does a chip need? Two to the power n locations need n lines. 1K needs 10 lines, 2K needs 11, 4K needs 12, and 8K needs 13. The full 64K of the 8085 needs all 16 lines.

| size | locations | address lines | lines used |
|---|---|---|---|
| 1K | 1024 | 10 | A0 – A9 |
| 2K | 2048 | 11 | A0 – A10 |
| 4K | 4096 | 12 | A0 – A11 |
| 8K | 8192 | 13 | A0 – A12 |
| 64K | 65536 | 16 | A0 – A15 |

### The 8085 side: the buses  (01:07)

Now the processor side. The lower address byte comes from AD0 to AD7 through the 74LS373 latch, using ALE. A8 to A15 come straight from the chip. And the data bus is AD0 to AD7 itself.

### Control: MEMR and MEMW  (01:24)

For control, we combine IO/M with RD and WR. When IO/M is low and RD is low, we get MEMR, memory read. When IO/M is low and WR is low, we get MEMW, memory write. A simple OR gate does each one, because all these signals are active low.

| IO/M̅ | R̅D̅ | M̅E̅M̅R̅ = OR |
|---|---|---|
| 0 | 0 | 0  (read memory) |
| 0 | 1 | 1 |
| 1 | 0 | 1  (I/O, not memory) |
| 1 | 1 | 1 |

### The idea of address decoding  (01:46)

Here is the main idea of decoding. The lower address lines, A0 to A12, go to every memory chip, to pick the location inside. The upper lines, A13 to A15, decide which chip is selected. A decoder turns them into chip select signals.

### The 74LS138 decoder  (02:03)

The 74LS138 is a 3 to 8 decoder. Its inputs C, B and A take A15, A14 and A13. It has three enables: G1 must be high, G2A and G2B must be low. Then exactly one of the outputs, Y0 to Y7, goes low.

### Each output = one 8K block  (02:24)

Each output covers one 8K block of the memory. Y0 is active from 0000H to 1FFFH, Y1 from 2000H to 3FFFH, and so on, up to Y7, from E000H to FFFFH. So we connect Y0 to the CS of the EPROM, and Y1 to the CS of the RAM.

### The complete circuit  (02:47)

Here is the complete circuit. The latch gives A0 to A7, and together with A8 to A12 they go to both chips. A13 to A15 go to the 74LS138. MEMR goes to OE of both chips, and MEMW goes to WE of the RAM. The data bus connects to both. To make sure the decoder works only for memory, IO/M is connected to the G2A enable.

### Check one address: 2050H  (03:15)

Let's check one address: 2050H. In binary, A15, A14 and A13 are 0, 0 and 1. That is input 1, so Y1 goes low, and the RAM is selected. The remaining thirteen bits give location 0050H inside the RAM.

### The address range of a chip  (03:34)

To find the address range of a chip, take the start address and add the size minus one. The RAM starts at 2000H, and its size is 8K, which is 2000H. So it ends at 2000H plus 2000H minus 1, which is 3FFFH.

### The memory map  (03:52)

This gives us the memory map. The EPROM sits at 0000H to 1FFFH. This is where the 8085 starts after reset. The RAM sits at 2000H to 3FFFH, for data and the stack. The rest, 4000H to FFFFH, is free for more chips.

### Absolute and partial decoding  (04:14)

One more point. When we use all the upper address lines for decoding, every location has exactly one address. This is called absolute decoding. If we leave some lines out, the circuit is cheaper, but each location appears at several addresses. This is partial, or linear, decoding, and it wastes address space.

### Summary  (04:34)

Here is the summary. The lower address lines go to every chip. The upper lines go to a decoder, which drives the chip selects. MEMR and MEMW come from IO/M, RD and WR. And the end address is the start plus the size minus one.

| signals | remember |
|---|---|
| A0 – A12 | to every chip:  the location |
| A13 – A15 | 74LS138  →  C̅S̅ of one chip |
| IO/M̅ + R̅D̅ / W̅R̅ | M̅E̅M̅R̅ / M̅E̅M̅W̅ |
| end address | start + size − 1 |
