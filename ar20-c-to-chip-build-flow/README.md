# ar20 · From C Code to the Chip

Follow a small LED program from C code all the way into the flash of an LPC1768 (ARM Cortex-M3): the compiler and object files, the sections .text, .rodata, .data and .bss, the linker script (scatter file in Keil), the map file, why .data has a load address in flash and a run address in RAM, the vector table, the LPC17xx checksum in word 7, what Reset_Handler does before main, the Intel hex format, and flashing with a debug adapter or the serial bootloader. Every number comes from a real build that was also run in an ARM emulator.

## Files

* [`startup.c`](startup.c) – the smallest startup code: vector table and a Reset_Handler that copies .data and clears .bss
* [`blink_main.c`](blink_main.c) – the LED program of the video (P0.22), with plain register addresses
* [`lpc1768.ld`](lpc1768.ld) – the linker script: flash at 0x00000000 (512 KB), RAM at 0x10000000 (32 KB)
* [`build_blink.sh`](build_blink.sh) – the whole path with the free LLVM tools: compile, link, size, bin, checksum, hex
* [`lpc_checksum.py`](lpc_checksum.py) – writes the LPC17xx checksum into word 7 of a .bin image

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### From C code to the chip  (00:00)

Today: what happens between your C code and the chip. We will follow a small LED program through the compiler, the linker, the hex file and the flash memory, and see what runs before main. Every number in this video comes from a real build for the LPC1768, which was also run in an ARM emulator.

### The whole path  (00:22)

Here is the whole path. The compiler turns each C file into an object file, the linker joins the object files into one executable, and a converter makes a hex file that is written into the flash. In Keil, the compiler is armclang, the linker is armlink, and the executable is the .axf file.

### Our example program  (00:43)

Our program blinks the LED on P0.22. It has three kinds of global data: blinks equal to 5, a variable with a starting value, count, a variable that starts at zero, and name, a constant string. And it uses the registers FIODIR0, FIOSET0 and FIOCLR0 at their fixed addresses.

### The compiler makes object files  (01:06)

The compiler turns each C file into an object file of Thumb-2 machine code. An object file cannot run yet: its addresses are not fixed, and calls to other files are left open. For example, startup.o calls main, but main is in main.o. Only the linker connects them.

### Sections  (01:26)

The compiler sorts everything into sections. .text holds the code, .rodata the constants, .data the variables with a starting value, and .bss the variables that start at zero. So blinks goes to .data, count goes to .bss, and name goes to .rodata. The build reports 282 bytes of code and constants, 4 bytes of data, and 4 bytes of bss.

| size |   |   |
|---|---|---|
| text | 282 bytes | code, vectors, constants |
| data | 4 bytes | blinks |
| bss | 4 bytes | count |

### The linker script  (01:54)

The linker must know where the memory is. The linker script, called a scatter file in Keil, says that the flash starts at 0x00000000 with 512 kilobytes, and the local SRAM starts at 0x10000000 with 32 kilobytes. Code and constants go to flash, while .data and .bss go to RAM. And the vector table is placed first, at address 0.

### The map file  (02:23)

The map file shows where everything ended up. The vector table is at 0, Reset_Handler at 0x40, and main at 0xA0. In RAM, blinks is at 0x10000000, and count right after it, at 0x10000004.

| address | symbol | memory |
|---|---|---|
| 0x00000000 | vector_table | flash |
| 0x00000040 | Reset_Handler | flash |
| 0x000000A0 | main | flash |
| 0x00000112 | name | flash |
| 0x10000000 | blinks | RAM |
| 0x10000004 | count | RAM |

### .data has two addresses  (02:41)

There is one trick. A RAM variable like blinks needs its starting value 5, but RAM forgets everything when the power goes off. So the linker stores the 5 in flash, right after the code, at 0x11C, and the start-up code copies it into RAM. That is why .data has two addresses: a load address in flash, and a run address in RAM.

### The vector table  (03:02)

Now the vector table. Word 0 is the initial stack pointer: 0x10008000, the top of the 32 kilobytes of RAM. Word 1 is the reset address: 0x00000041, which is Reset_Handler at 0x40, plus 1 for Thumb. The other words point to the exception handlers.

| word | address | value | meaning |
|---|---|---|---|
| 0 | 0x00000000 | 0x10008000 | initial stack pointer |
| 1 | 0x00000004 | 0x00000041 | reset: Reset_Handler + 1 |
| 2 | 0x00000008 | 0x0000009B | NMI handler |
| 3 | 0x0000000C | 0x0000009B | HardFault handler |
| … |  |  |  |
| 7 | 0x0000001C | ? | LPC17xx checksum |

### The LPC1768 checksum  (03:25)

The LPC1768 adds one more rule. Word 7 must make the sum of the first eight words zero, or the chip will not start the program. Here word 7 is 0xEFFF7CB8. Keil and Flash Magic fill it in automatically, so now you know why that word is never zero in a real image.

### What runs before main()  (03:47)

At reset, the processor loads word 0 into SP and word 1 into PC, so Reset_Handler runs first. Our Reset_Handler copies .data from flash to RAM, clears .bss, and only then calls main. In a Keil project, the same work is done by the startup file and the library function __main. So when main starts, blinks is already 5, and count is already 0.

### The Intel hex file  (04:13)

To put the program into the chip, the executable is converted into a hex file. Every line of an Intel hex file is a record: a colon, the number of bytes, the address, the type, the data, and a checksum. The first line here holds 16 bytes for address 0: the stack pointer, the reset address and two handler addresses, each word with its lowest byte first. A .bin file holds the same bytes, without addresses.

### Writing the flash  (04:41)

Finally the bytes are written into the flash. With a debug adapter on JTAG or SWD, Keil programs the flash and can start debugging at once. Or the built-in bootloader of the LPC1768 takes the hex file over the serial port, with Flash Magic.

### The real image in an emulator  (04:59)

We ran this exact image on an emulated Cortex-M3. Reset_Handler copied 5 into blinks, and main wrote 0x00400000 to FIODIR0, and then to FIOSET0 and FIOCLR0, again and again. On a board, the LED on P0.22 blinks five times.

| register | address | value written |
|---|---|---|
| FIODIR0 | 0x2009C000 | 0x00400000 |
| FIOSET0 | 0x2009C018 | 0x00400000 |
| FIOCLR0 | 0x2009C01C | 0x00400000 |
| FIOSET0 | 0x2009C018 | 0x00400000 |
| FIOCLR0 | 0x2009C01C | 0x00400000 |

### Practice  (05:24)

Now try this yourself. Pause the video. We add a new global variable: int limit equal to 100. Which section does it go to, and where is its value 100 kept? The answer: limit goes to .data in RAM, and its starting value is kept in flash, and copied by the start-up code.

### Summary  (05:43)

Here is the summary. The compiler makes object files with sections, and the linker places them, following the linker script. Code and constants stay in flash, while .data and .bss live in RAM, with the starting values of .data copied from flash. The vector table at address 0 gives the stack pointer and the reset address, and the LPC1768 also checks word 7. Reset_Handler prepares RAM before main, and the hex file carries the bytes into the flash.

|   | remember |
|---|---|
| compiler | C → object files with sections |
| linker | places the sections, linker script / scatter file |
| flash | .text, .rodata, starting values of .data |
| RAM | .data, .bss, stack |
| vector table | word 0 = SP, word 1 = reset;  LPC1768: word 7 checksum |
| Reset_Handler | copy .data, clear .bss, then main() |
| hex file | carries the bytes into the flash |
