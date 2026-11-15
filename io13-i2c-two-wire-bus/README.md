# io13 · I2C Explained

I2C from the wires to the registers: SDA and SCL, open drain and pull-up resistors (the wired AND), START and STOP conditions, 8 bits plus ACK or NACK, the address byte with R/W (0x48 gives 0x90 and 0x91), writing and reading a register with a repeated START, clock stretching, arbitration and speeds, the I2C2 block of the LPC1768 (P0.10, P0.11, open drain, I2C2SCLH/SCLL), its state machine with SI and status codes 0x08, 0x18, 0x28, 0x10, 0x40, 0x50, 0x58, the read function, the bus seen by an emulated Cortex-M3 with a model of the controller and an LM75 sensor (25.5 degrees), strengths and limits, and a practice question.

## Files

* [`i2c_demo.c`](i2c_demo.c) – I2C master on the LPC1768 (I2C2: SDA2 = P0.10, SCL2 = P0.11, 100 kHz, polling)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_i2c.py`](test_i2c.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_i2c.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### I2C: the two-wire bus  (00:00)

Today: I2C, the two-wire bus that connects sensors, memories, clocks and displays to a microcontroller. We will see the two open-drain wires and their pull-up resistors, the start and stop conditions, addresses and acknowledge bits, how a register is written and read, and the I2C block of the LPC1768 with its status codes. The code reads a temperature sensor, and on an emulated Cortex-M3 with a model of the I2C controller and the sensor, it read 25.5 degrees.

### Two wires for many devices  (00:35)

I2C needs only two wires for any number of devices: SDA carries the data, and SCL carries the clock. Every device sits on the same two wires, and each slave has its own 7-bit address. The master starts every transfer and drives the clock. Sensors, EEPROMs, real-time clocks and small displays all use I2C.

### Open drain and pull-ups  (01:00)

The two wires are open drain: a device can only pull a line low, or let it go. A pull-up resistor, typically 4.7 kilohms, brings the line high when nobody pulls it. So if any device pulls the line low, it is low, and two devices can never fight, because nobody drives it high. This is called a wired AND.

### START and STOP  (01:24)

Normally, SDA may only change while SCL is low. The two exceptions mark the start and the end of a transfer. A START condition is SDA falling while SCL is high, and a STOP condition is SDA rising while SCL is high. Between them, the bus belongs to the master that started it.

### 8 bits + ACK  (01:45)

Every byte is sent as 8 bits, the most significant bit first, followed by a ninth clock for the acknowledge bit. On that ninth clock, the receiver pulls SDA low to say: got it, this is an ACK. If SDA stays high, that is a NACK, which means that no device answered, or that the receiver wants no more bytes. So each byte takes 9 clocks.

### The address byte  (02:11)

The first byte after a START is the address byte: the 7-bit slave address, followed by one more bit, R/W. A 0 means the master wants to write, and a 1 means it wants to read. For a sensor at address 0x48, the address byte is 0x90 for writing, and 0x91 for reading. Only the slave with that address answers with an ACK.

### Writing a register  (02:35)

To write a register, the master sends START, the address with W, the register number, and then the data bytes, each one acknowledged by the slave. Then it sends STOP. Many devices then move to the next register by themselves, so several bytes can follow.

### Reading a register  (02:52)

Reading a register takes two steps. First the master writes the register number: START, address with W, register. Then, without a STOP, it sends a repeated START and the address with R, and the slave starts sending bytes. The master answers ACK to every byte it wants more of, NACK to the last one, and then STOP.

### Stretching, arbitration, speeds  (03:14)

Two more features come from the open-drain wires. A slow slave can hold SCL low to make the master wait, and this is called clock stretching. And if two masters start at once, the one that sends a 1 while the line is 0 notices it and steps back: this is arbitration. The usual speeds are 100 kilohertz, 400 kilohertz, and 1 megahertz in fast mode plus.

| mode | speed |
|---|---|
| standard | 100 kHz |
| fast | 400 kHz |
| fast plus | 1 MHz |

### I2C on the LPC1768  (03:38)

The LPC1768 has three I2C blocks. Here we use I2C2, with SDA2 on P0.10 and SCL2 on P0.11. These pins must be set to open drain in PINMODE_OD0, with external pull-up resistors. The clock is set by I2C2SCLH and I2C2SCLL, the high and low times in peripheral clock cycles: 125 plus 125 gives 25 megahertz divided by 250, which is 100 kilohertz.

| signal | pin | function |
|---|---|---|
| SDA2 | P0.10 | PINSEL0 bits 21:20 = 10 |
| SCL2 | P0.11 | PINSEL0 bits 23:22 = 10 |

### A state machine with status codes  (04:12)

The I2C block works as a state machine. The program sets STA in I2C2CONSET to send a START, writes bytes into I2C2DAT, and sets STO to send a STOP. After every bus event, the hardware sets the SI flag, and puts a status code into I2C2STAT that says what just happened. The program checks the code, and clears SI in I2C2CONCLR to start the next step.

### Status codes for a read  (04:41)

Here are the codes for a register read. 0x08 means START sent, 0x18 address with W sent and ACK received, 0x28 data sent and ACK received, and 0x10 repeated START sent. 0x40 means address with R sent and ACK received, 0x50 a byte received and ACK returned, and 0x58 a byte received and NACK returned.

| I2C2STAT | meaning |
|---|---|
| 0x08 | START sent |
| 0x18 | address + W sent, ACK received |
| 0x28 | data sent, ACK received |
| 0x10 | repeated START sent |
| 0x40 | address + R sent, ACK received |
| 0x50 | byte received, ACK returned |
| 0x58 | byte received, NACK returned |

### The read function  (05:09)

Here is the read function. Each step writes the next byte or flag, clears SI, waits for SI again, and compares I2C2STAT with the expected code. If any code is wrong, for example 0x20 when no device answers, the function sends a STOP and returns that code. For the last byte, it clears AA, so that the master answers NACK.

### On the emulator  (05:36)

On the emulator, the setup wrote 0x00A00000 into PINSEL0, set bits 10 and 11 of PINMODE_OD0 with 0x00000C00, and wrote 125 into both SCL registers. Then the model of the bus and of an LM75 sensor saw exactly the planned sequence: START, address 0x48 with W, register 0, repeated START, address with R. The sensor sent 0x19 and 0x80, and the master answered ACK and then NACK, with the status codes 0x50 and 0x58. 0x19 is 25 degrees, and the top bit of 0x80 adds half a degree, so the result is 25.5 degrees. With the sensor removed, the address got a NACK, the status was 0x20, and the function stopped cleanly.

| register | write |
|---|---|
| PINSEL0 | 0x00A00000 |
| PINMODE_OD0 | 0x00000C00 |
| I2C2SCLH | 0x0000007D |
| I2C2SCLL | 0x0000007D |

| bus event | status |
|---|---|
| START | 0x08 |
| 0x48 + W, ACK | 0x18 |
| register 0, ACK | 0x28 |
| repeated START | 0x10 |
| 0x48 + R, ACK | 0x40 |
| 0x19, master ACK | 0x50 |
| 0x80, master NACK | 0x58 |
| STOP |  |

### Strengths and limits  (06:31)

So I2C needs only two wires for many devices, has addresses and acknowledge bits, and is supported by thousands of chips. It is slower than SPI, half duplex, and the pull-ups limit the speed and the length of the wires. It fits sensors and configuration data on one board perfectly.

### Practice  (06:51)

Now try this yourself. Pause the video. An EEPROM has the 7-bit address 0x50. Which address bytes does the master send to write to it, and to read from it? 0x50 shifted left by one is 0xA0 for writing, and with the R/W bit set, 0xA1 for reading.

### Summary  (07:11)

Here is the summary. I2C uses two open-drain wires, SDA and SCL, with pull-up resistors, and 7-bit addresses. START and STOP are SDA changes while SCL is high, and every byte is followed by an ACK or a NACK. A register read is: START, address with W, register, repeated START, address with R, the bytes, NACK, STOP. On the LPC1768, every step sets SI and leaves a status code in I2C2STAT.

|   | remember |
|---|---|
| wires | SDA, SCL: open drain + pull-ups; 7-bit addresses |
| framing | START / STOP: SDA changes while SCL is high |
| bytes | 8 bits + ACK or NACK |
| read | S, addr+W, reg, Sr, addr+R, bytes, NACK, P |
| LPC1768 | every step: SI = 1 and a code in I2C2STAT |
