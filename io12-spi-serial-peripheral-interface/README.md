# io12 · SPI Explained

SPI from the wires to the registers: SCK, MOSI, MISO and chip select, two shift registers that swap their bytes, why reading needs a dummy byte, CPOL, CPHA and the four SPI modes, MSB first and no acknowledge, several slaves with their own select lines, the SPI block of the LPC1768 (S0SPCR, S0SPSR, S0SPDR, S0SPCCR), the setup and transfer code, reading the 3-byte ID of a SPI flash with the command 0x9F, the values seen on an emulated Cortex-M3 with a model of the flash (0x00EF4018), the waveform of 0x9F in mode 0, strengths and limits, and a practice question.

## Files

* [`spi_demo.c`](spi_demo.c) – SPI master on the LPC1768: read the 3-byte ID of a SPI flash memory (command 0x9F)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_spi.py`](test_spi.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_spi.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### SPI: the serial peripheral interface  (00:00)

Today: SPI, the serial peripheral interface, the fast and simple link between a microcontroller and chips like flash memories, displays, sensors and SD cards. We will see its four wires, how two shift registers swap their bytes, the four SPI modes, how to talk to several chips, and the SPI block of the LPC1768. The code reads the ID of a flash memory, and on an emulated Cortex-M3 with a model of the flash, it got the right answer.

### Four wires  (00:32)

SPI uses four wires. SCK is the clock, and it always comes from the master. MOSI, master out slave in, carries data to the slave, and MISO, master in slave out, carries data back. The fourth wire, chip select, often written CS or SS, is pulled low by the master to choose the slave it wants to talk to.

### Two shift registers in a ring  (00:55)

Inside, the master and the slave each have an 8-bit shift register, and the two are connected in a ring. On every clock pulse, each side pushes one bit out and takes one bit in. After 8 clocks, the two bytes have changed places. So every transfer is a send and a receive at the same time: SPI is full duplex.

### To read, you must write  (01:16)

This has an important consequence: to receive a byte, the master must send one. When it only wants to read, it sends a dummy byte, often 0xFF, just to make the clock run. Whatever the slave had in its register comes back at the same time.

### CPOL, CPHA: four SPI modes  (01:32)

Two settings decide when the bits are read. CPOL is the idle level of the clock: 0 means low, and 1 means high. CPHA says whether data is read on the first or the second clock edge. Together they give four SPI modes, and mode 0, with the clock idle low and data read on the rising edge, is the most common.

### MSB first, no addresses, no acknowledge  (01:54)

Usually the most significant bit goes first. Unlike I2C, there are no addresses and no acknowledge bits: the chip select line alone says who is meant, and the master simply trusts that the slave is there. This keeps SPI simple and fast, often 10 megahertz or more, but only over short distances on a board.

### Several slaves  (02:16)

With several slaves, MOSI, MISO and SCK are shared, and each slave gets its own chip select line. Only the selected slave drives MISO, and the others leave it free. So 3 slaves need 3 select lines, and 6 wires in total.

### SPI on the LPC1768  (02:32)

The LPC1768 has a simple SPI block, and two SSP blocks that also speak SPI. The simple SPI uses P0.15 for SCK, P0.17 for MISO and P0.18 for MOSI. Its clock is the peripheral clock divided by S0SPCCR, which must be an even number of at least 8. With 25 megahertz and 8, SCK runs at 3.125 megahertz.

| signal | pin |
|---|---|
| SCK | P0.15 |
| MISO | P0.17 |
| MOSI | P0.18 |
| CS (GPIO) | P0.16 |

### The SPI registers  (03:02)

S0SPCR is the control register: bit 3 is CPHA, bit 4 is CPOL, bit 5 makes it the master, and bit 6 selects the least significant bit first. S0SPDR is the data register, and S0SPSR holds the status, with bit 7, SPIF, set when a transfer is complete. For chip select, many programs simply use a GPIO pin, here P0.16.

### Setup and transfer  (03:30)

Here is the setup. PINSEL0 and PINSEL1 select SCK, MISO and MOSI, and P0.16 becomes a GPIO output that starts high, so that no chip is selected. S0SPCCR gets 8, and S0SPCR gets 0x20: master, mode 0, 8 bits, most significant bit first. spi_transfer writes a byte into S0SPDR, waits for SPIF, and returns the byte that came back.

### Reading the ID of a SPI flash  (04:02)

Now a real job: reading the ID of a SPI flash memory. We pull chip select low and send the command 0x9F. Then we send three dummy bytes, and with each one, the flash sends back one byte of its ID: the maker, the memory type and the capacity. Finally, chip select goes high again.

### On the emulator  (04:23)

On the emulator, the setup wrote 0xC0000000 into PINSEL0, 0x0000003C into PINSEL1, 8 into S0SPCCR, and 0x00000020 into S0SPCR. Then a model of the flash watched the bus. With chip select low, it saw 0x9F on MOSI, and answered the three dummy bytes with 0xEF, 0x40 and 0x18 on MISO. So flash_read_id returned 0x00EF4018, the ID of a common 128 megabit flash chip.

| register | write |
|---|---|
| PINSEL0 | 0xC0000000 |
| PINSEL1 | 0x0000003C |
| S0SPCCR | 0x00000008 |
| S0SPCR | 0x00000020 |

| byte | MOSI | MISO |
|---|---|---|
| CS low |  |  |
| 1 | 0x9F | 0xFF |
| 2 | 0xFF | 0xEF |
| 3 | 0xFF | 0x40 |
| 4 | 0xFF | 0x18 |
| CS high |  |  |

### 0x9F on the wires  (05:00)

Here is the command byte on the wires. Chip select goes low, then 8 clock pulses shift out 1001 1111, which is 0x9F, most significant bit first. In mode 0, the data changes on the falling edge, and is read on the rising edge.

### Strengths and limits  (05:19)

So SPI is fast, full duplex, simple to drive, and needs no addresses. On the other hand, it uses more wires than I2C, needs one select line per slave, and has no acknowledge, so the master cannot even tell whether a slave is connected. It suits short, fast links on one board.

### Practice  (05:39)

Now try this yourself. Pause the video. SCK runs at 3.125 megahertz. How long does it take, at least, to read 256 bytes from the flash? 256 bytes are 2048 bits, and 2048 divided by 3.125 million is about 655 microseconds, and the real time is a little longer, because of the command byte and the gaps between bytes.

### Summary  (06:06)

Here is the summary. SPI has four wires: SCK and chip select from the master, MOSI out and MISO in. Two shift registers swap their bytes, so every transfer sends and receives, and reading needs a dummy byte. CPOL and CPHA give four modes, and mode 0 is the most common. On the LPC1768, set S0SPCCR and S0SPCR, write S0SPDR, wait for SPIF, and read S0SPDR.

|   | remember |
|---|---|
| wires | SCK, CS from the master; MOSI out, MISO in |
| transfer | shift registers swap bytes; read = send a dummy |
| modes | CPOL, CPHA: 4 modes; mode 0 most common |
| LPC1768 | S0SPCCR, S0SPCR; write S0SPDR, wait SPIF, read S0SPDR |
