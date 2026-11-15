# io16 · 1-Wire Explained

1-Wire from the line to the temperature: one open-drain data line with a pull-up, parasite power, unique 64-bit ROM codes, reset and presence pulses, write and read time slots, ROM commands (Skip, Match, Search, Read ROM), the DS18B20 with Convert T and Read Scratchpad, bit-banging on a GPIO pin of the LPC1768 with Timer0 microsecond delays, the slot functions and the temperature function, an emulated Cortex-M3 with a timed model of the line and a DS18B20 that read 25.0625 degrees, the Dallas / Maxim CRC-8, strengths and limits, and a practice question.

## Files

* [`onewire_demo.c`](onewire_demo.c) – 1-Wire master by bit-banging a GPIO pin (LPC1768): read a DS18B20 temperature sensor
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_onewire.py`](test_onewire.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_onewire.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### 1-Wire: one data wire  (00:00)

Today: 1-Wire, the bus that needs only one data wire and a ground, made popular by temperature sensors like the DS18B20. We will see the open-drain line, the reset and presence pulses, the time slots that carry each bit, the 64-bit ROM codes, the commands, and how to read a temperature by bit-banging a GPIO pin of the LPC1768. On an emulated Cortex-M3 with a timed model of the line and the sensor, the code read 25.0625 degrees.

### One data line, one ground  (00:33)

A 1-Wire bus has a single data line, called DQ, plus ground, and one master with any number of slaves. Like I2C, the line is open drain: a 4.7 kilohm resistor pulls it up, and every device can only pull it low. There is no clock wire at all: the meaning of every bit comes from how long the line stays low. Some devices can even take their power from the data line, which is called parasite power.

### A unique 64-bit ROM code  (01:01)

Every 1-Wire device has a unique 64-bit ROM code, burned in at the factory. The first byte is the family code, for example 0x28 for the DS18B20, then come 48 bits of serial number, and a last byte with a CRC. So the master can address any single device on a long line, without any setup. And the Search ROM command lets the master find all the codes on the bus.

### Reset and presence  (01:27)

Every transaction starts with a reset. The master pulls the line low for at least 480 microseconds, and then releases it. Every device on the bus answers by pulling the line low for 60 to 240 microseconds: this is the presence pulse. So the master knows whether anybody is there.

### Write slots  (01:47)

Bits are sent in time slots of about 60 microseconds, the least significant bit first. To write a 1, the master pulls the line low only briefly, for a few microseconds, and releases it. To write a 0, it holds the line low for the whole slot, at least 60 microseconds. The slave samples the line about 15 to 30 microseconds after the falling edge, and so it sees a 1 or a 0.

### Read slots  (02:13)

To read a bit, the master again pulls the line low for a few microseconds, and releases it. If the slave wants to send a 0, it keeps the line low for a while. If it sends a 1, it does nothing, and the pull-up raises the line. The master reads the line about 15 microseconds after the falling edge.

### ROM commands  (02:33)

After the reset, the master sends a ROM command that chooses the device. Skip ROM, 0xCC, talks to all devices at once, which is fine when there is only one. Match ROM, 0x55, followed by a 64-bit code, selects one device, and Search ROM, 0xF0, finds them all. Then follows a function command for the selected device.

| code | command | meaning |
|---|---|---|
| 0xCC | Skip ROM | all devices (fine for one) |
| 0x55 | Match ROM | + 64-bit code: one device |
| 0xF0 | Search ROM | find all codes |
| 0x33 | Read ROM | read the code (one device only) |

### The DS18B20  (02:58)

For the DS18B20, two function commands are enough. Convert T, 0x44, starts a temperature measurement, which takes up to 750 milliseconds at 12 bits, and the sensor sends 0s in read slots until it is done. Read Scratchpad, 0xBE, then returns 9 bytes: the temperature in the first two, a few settings, and a CRC in the last byte. The temperature is a signed number in sixteenths of a degree.

| byte | content |
|---|---|
| 0 | temperature LSB |
| 1 | temperature MSB |
| 2, 3 | alarm limits TH, TL |
| 4 | configuration |
| 5 .. 7 | reserved |
| 8 | CRC |

### Bit-banging on the LPC1768  (03:26)

The LPC1768 has no 1-Wire hardware, so we bit-bang it on a GPIO pin, here P0.4. The output latch of the pin is set to 0 once, and never changed. Making the pin an output in FIODIR0 pulls the line low, and making it an input releases it, so the pin never drives the line high. Precise delays come from Timer0 counting in microseconds, and interrupts should be off during a slot, so that the timing is not stretched.

### The slot functions  (03:57)

Here are the slot functions. ow_reset holds the line low for 480 microseconds, releases it, and looks for the presence pulse after 70 microseconds. ow_write_bit holds the line low for 6 microseconds for a 1, or 60 for a 0. ow_read_bit pulls low for 6 microseconds, releases, and reads the line 9 microseconds later, at 15 microseconds into the slot.

### Reading the temperature  (04:26)

The temperature function puts it all together. Reset, Skip ROM, Convert T, and read slots until the sensor sends a 1. Then reset, Skip ROM, Read Scratchpad, 9 bytes, a CRC check, and the first two bytes form the temperature.

### On the emulator  (04:44)

On the emulator, delay_us did not wait for real, but moved a virtual clock forward, and a model of the line and of a DS18B20 watched every edge. It saw a reset of 480 microseconds and answered with a presence pulse, then received the commands 0xCC and 0x44. After the second reset, it received 0xCC and 0xBE, and sent its 9 scratchpad bytes, starting with 0x91 and 0x01. The CRC of the 8 data bytes matched the ninth byte, 0x25, and 0x0191 is 401 sixteenths, which is 25.0625 degrees. With the sensor removed, there was no presence pulse, and the function returned its error code.

| event | seen by the model |
|---|---|
| reset 480 µs | presence pulse |
| write byte | 0xCC  (Skip ROM) |
| write byte | 0x44  (Convert T) |
| reset 480 µs | presence pulse |
| write bytes | 0xCC, 0xBE |
| read 9 bytes | 0x91 0x01 0x4B 0x46 0x7F 0xFF 0x0F 0x10 0x25 |

### CRC-8  (05:30)

The CRC is the Dallas, or Maxim, CRC-8, with the polynomial x to the 8, plus x to the 5, plus x to the 4, plus 1. It is computed bit by bit, with a shift and an exclusive OR with 0x8C. A wrong CRC means that a bit was damaged on the long wire, so the program reads again.

### Strengths and limits  (05:54)

So 1-Wire needs the fewest wires of all, gives every device a unique address, and can even power small sensors through the data line. But it is slow, about 16 kilobits per second, and the timing must be kept to a few microseconds. It is perfect for temperature sensors spread along a long cable, and for ID chips.

### Practice  (06:16)

Now try this yourself. Pause the video. A DS18B20 returns the two temperature bytes 0x50 and 0x05. What is the temperature? The first byte is the low byte, so the value is 0x0550, which is 1360, and 1360 divided by 16 is 85 degrees, which is also the value the sensor reports right after power-up, before its first conversion.

### Summary  (06:45)

Here is the summary. 1-Wire uses one open-drain data line with a pull-up, and every device has a unique 64-bit ROM code. A reset pulse of 480 microseconds is answered by presence pulses, and every bit is a time slot: a short low pulse is a 1, and a long one is a 0. A transaction is a reset, a ROM command like Skip ROM, and a function command like Convert T or Read Scratchpad. On the LPC1768, a GPIO pin switched between output low and input, with microsecond delays, does the job.

|   | remember |
|---|---|
| line | one open-drain wire + pull-up; 64-bit ROM codes |
| reset | 480 µs low → presence pulses |
| bits | time slots: short low = 1, long low = 0 |
| transaction | reset, ROM command, function command |
| LPC1768 | GPIO: output low / input, µs delays |
