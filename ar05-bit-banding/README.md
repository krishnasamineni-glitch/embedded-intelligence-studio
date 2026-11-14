# ar05 · ARM Cortex-M3 Bit-Banding Explained

Why is changing one bit dangerous, and how does bit-banding solve it? We look at read-modify-write and the race with an interrupt, the two bit-band regions and their alias regions, the alias address formula, two worked examples (SRAM and an LPC1768 GPIO pin), a C macro for bit-banding, and practice problems.

## Files

* [`bitband.h`](bitband.h) – BITBAND macros (the one from the video, and a version for both regions)
* [`bitband_demo.c`](bitband_demo.c) – blink P0.22 with one bit-band store (LPC1768, Keil + CMSIS)
* [`alias_calc.py`](alias_calc.py) – alias address calculator, shows every step of the formula

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Bit-banding  (00:00)

Today: bit-banding in the Cortex-M3. We will see why changing a single bit is a problem, how bit-banding solves it, how to calculate a bit-band alias address step by step, and how to use it from C on the LPC1768.

### Read-modify-write  (00:18)

Suppose we want to set bit 2 of a variable in RAM. Normally this takes three instructions: load the word, OR it with the bit, and store it back. This is called read-modify-write.

### The race with an interrupt  (00:30)

And there is a danger. If an interrupt arrives between the load and the store, and the interrupt handler changes another bit of the same word, our store writes back the old value, and the handler's change is lost. Bugs like this are rare, and very hard to find.

### The idea: one word per bit  (00:48)

Bit-banding solves this. Every single bit in a bit-band region gets its own 32-bit word, at an address in a second region, called the alias region. Writing 1 to that word sets the bit, and writing 0 clears it. Reading it gives 0 or 1. The bus does the read-modify-write by itself, in one step that nothing can interrupt.

### The two bit-band regions  (01:10)

There are two bit-band regions. The first megabyte of the SRAM region, from 0x20000000 to 0x200FFFFF, has its alias region at 0x22000000. And the first megabyte of the peripheral region, from 0x40000000, has its alias region at 0x42000000. Each alias region is 32 MB, because every bit needs a word of 4 bytes: 1 MB times 8 bits times 4 bytes.

|   | bit-band region (1 MB) | alias region (32 MB) |
|---|---|---|
| SRAM | 0x20000000 – 0x200FFFFF | 0x22000000 – 0x23FFFFFF |
| peripheral | 0x40000000 – 0x400FFFFF | 0x42000000 – 0x43FFFFFF |

### The alias formula  (01:45)

Here is the formula. Alias address equals alias base, plus byte offset times 32, plus bit number times 4. The byte offset is the address minus the start of the bit-band region. Times 32, because every byte has 8 bits, and every bit takes 4 bytes. And times 4, to step to the right bit.

### Example 1  (02:06)

Example one: bit 2 of the byte at 0x20000300. The byte offset is 0x300. 0x300 times 32 is 0x6000. Bit 2 times 4 is 8. So the alias address is 0x22000000 plus 0x6000 plus 8, which is 0x22006008.

### Using the alias word  (02:33)

Now, writing 1 to address 0x22006008 sets bit 2 of the byte at 0x20000300, and writing 0 clears it. The other seven bits are not touched. And reading 0x22006008 tells us whether the bit is 0 or 1.

### Example 2: LPC1768 P0.22  (02:54)

Example two, on the LPC1768: pin P0.22, which is bit 22 of the GPIO register FIO0PIN, at 0x2009C014. This address is inside the SRAM bit-band region. The byte offset is 0x9C014. Times 32 gives 0x1380280. Bit 22 times 4 is 88, which is 0x58. So the alias address is 0x233802D8.

### Word bit vs byte bit  (03:26)

Notice that the bit number can go up to 31 for a whole word. Bit 22 of the word is simply bit 6 of its third byte, and the formula lands on exactly the same alias address.

### Bit-banding in C  (03:37)

In C, we write a small macro that turns an address and a bit number into a pointer to the alias word. Then BITBAND(0x2009C014, 22) = 1 makes P0.22 high, and = 0 makes it low. The pointer must be volatile, so that the compiler really writes to it every time.

### Compare the two ways  (03:59)

Compare the two ways. Read-modify-write needs three instructions and can be broken by an interrupt. The bit-band write is one store instruction, and it is atomic.

### A warning  (04:10)

One warning. Bit-banding works only in these two 1 MB regions. On the LPC1768, the 32 KB local SRAM at 0x10000000 is in the code region, so it has no bit-band alias. Variables that need bit-banding should go into the AHB SRAM at 0x2007C000.

| LPC1768 memory | address | region | bit-band? |
|---|---|---|---|
| local SRAM 32 KB | 0x10000000 | code region | no |
| AHB SRAM 2 × 16 KB | 0x2007C000 | SRAM bit-band | yes |
| fast GPIO | 0x2009C000 | SRAM bit-band | yes |
| APB peripherals | 0x40000000 | peripheral bit-band | yes |

### Practice  (04:34)

Now try these yourself. Pause the video. One: bit 7 of the byte at 0x20000004. Two: bit 0 of the peripheral register at 0x40004000. The answers are: 0x2200009C, and 0x42080000.

### Summary  (04:58)

Here is the summary. Bit-banding gives every bit of the first megabyte of SRAM and of peripherals its own word. The alias address is the alias base plus byte offset times 32 plus bit number times 4. One store sets or clears the bit, atomically, without touching the other bits.

|   | remember |
|---|---|
| regions | first 1 MB of SRAM (0x20000000) and of peripherals (0x40000000) |
| alias | 0x22000000 / 0x42000000, one word per bit |
| formula | base + byte offset × 32 + bit number × 4 |
| benefit | one store, atomic, other bits untouched |
