# io17 · UART vs SPI vs I2C vs CAN vs USB vs 1-Wire

The communication buses side by side: how many wires each needs, which carry a clock and which are full or half duplex, typical speeds, how far each reaches (including RS-485), how devices are chosen (chip select, addresses, message identifiers, enumeration), how errors are detected (parity, ACK, CRC, automatic repeat), one summary table, how to choose with real examples, several buses on one LPC1768 board, and a practice question.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Six buses side by side  (00:00)

Today: UART, SPI, I2C and CAN side by side, with USB and 1-Wire as well. We will compare their wires, speeds, distances, numbers of devices and error handling. And then, with a few real examples, we will see how to choose the right one for a job.

### Wires  (00:21)

Start with the wires. UART needs two signal wires, TX and RX, for one partner. SPI needs four, and one more select line for every extra slave. I2C needs two for the whole bus, CAN two for the whole network, and 1-Wire only one.

### Clock wire and duplex  (00:40)

Next, the timing. SPI and I2C send a clock wire with the data, while UART, CAN, USB and 1-Wire recover the timing from the data itself. SPI and UART are full duplex, and I2C, CAN, USB and 1-Wire are half duplex.

| bus | clock wire? | duplex |
|---|---|---|
| UART | no: agreed baud | full |
| SPI | yes: SCK | full |
| I2C | yes: SCL | half |
| CAN | no: edges | half |
| USB | no: NRZI + SYNC | half |
| 1-Wire | no: time slots | half |

### Speed  (01:00)

Then the speed. SPI is the fastest of the simple buses, often 10 to 50 megabits per second. I2C runs at 100 or 400 kilobits, sometimes 1 megabit, and CAN up to 1 megabit per second, with CAN FD faster in its data phase. UART usually runs from 9600 baud to about 1 megabit per second, USB full speed at 12 megabits, and 1-Wire at about 16 kilobits.

### Distance  (01:29)

Distance matters too. SPI and I2C are meant for one board, a few tens of centimetres. CAN reaches 40 metres at 1 megabit and hundreds of metres when slower, RS-485 even 1200 metres, while 1-Wire can run along tens of metres of cable.

### Finding each other  (01:50)

How do devices find each other? UART connects exactly two. SPI picks a slave with a chip select line, so every slave costs a pin. I2C and 1-Wire use addresses, 7 bits and 64 bits, and CAN uses message identifiers instead, so any node can listen to any message, while USB hands out addresses itself, during enumeration.

| bus | how a device is chosen |
|---|---|
| UART | exactly two devices |
| SPI | a chip select line per slave |
| I2C | 7-bit address |
| 1-Wire | 64-bit ROM code |
| CAN | message identifiers: anyone may listen |
| USB | addresses given at enumeration |

### Error handling  (02:16)

Error handling differs a lot. SPI has none at all, UART at most a parity bit, and I2C an acknowledge after every byte. CAN and USB protect every message with a CRC and repeat it automatically, and 1-Wire devices add a CRC-8 to their data.

| bus | checks |
|---|---|
| SPI | none |
| UART | parity bit (optional) |
| I2C | ACK after every byte |
| CAN | CRC-15, ACK, automatic repeat, error counters |
| USB | CRC, ACK / NAK, automatic repeat |
| 1-Wire | CRC-8 in the data |

### One table, and how to choose  (02:34)

Here is everything in one table. Pause the video if you want to keep it.

|   | wires | clock | duplex | speed | distance | devices | errors |
|---|---|---|---|---|---|---|---|
| UART | 2 | no | full | ≤ 1 Mbit/s | ≈ 1 m | point-to-point | parity |
| SPI | 4 + CS | yes | full | 10–50 Mbit/s | board | chip select | none |
| I2C | 2 | yes | half | 0.1–1 Mbit/s | board | 7-bit address | ACK |
| CAN | 2 diff. | no | half | ≤ 1 Mbit/s | 40–500 m | identifiers | CRC, ACK |
| USB | 2 diff. | no | half | 12 / 480 Mbit/s | 5 m | host assigns | CRC, ACK |
| 1-Wire | 1 | no | half | 16 kbit/s | tens of m | 64-bit ROM | CRC-8 |

### How to choose

So how do we choose? A display or an SD card that needs speed on the same board: SPI. Several sensors and a real-time clock with few pins: I2C. Debug messages to a PC, or a GPS or Bluetooth module: UART. Many control units in a car or a machine, with long wires and noise: CAN, and temperature sensors spread along a long cable: 1-Wire.

### Several buses on one board  (03:06)

Real products often use several at once. A typical board might read sensors over I2C, store the data in SPI flash, print debug messages over a UART, and talk to a PC over USB. The LPC1768 alone has UARTs, SPI, I2C, CAN and USB built in.

### Practice  (03:30)

Now try this yourself. Pause the video. A machine has 10 control units, spread over 30 metres of a noisy factory floor. Which bus fits, and why? CAN: it is a differential bus that resists noise, reaches 30 metres easily, lets every unit send, and checks every message with a CRC.

### Summary  (03:51)

Here is the summary. Fewest wires: 1-Wire, then I2C and CAN with two. Fastest on a board: SPI, with no addresses and no error checks. Longest and most robust: CAN and RS-485, with differential pairs, and the simplest point-to-point link is the UART.

|   | choose |
|---|---|
| fewest wires | 1-Wire; then I2C and CAN (two) |
| fastest on a board | SPI: no addresses, no checks |
| longest, most robust | CAN and RS-485: differential pairs |
| simplest link | UART: point-to-point |
