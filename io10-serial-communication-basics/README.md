# io10 · Serial Communication Basics

The ideas behind every communication protocol: parallel and serial links, skew and crosstalk, synchronous and asynchronous timing, the asynchronous frame (start bit, data bits least significant first, parity, stop bit, 8N1), reading each bit in its middle, baud rate and throughput (9600 baud = 104 us per bit = 960 bytes/s), simplex, half and full duplex, parity, checksums and CRC, point-to-point links and buses, logic, RS-232 and differential levels, how UART, SPI, I2C, CAN, USB and 1-Wire fit these ideas, and a practice question.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Serial communication basics  (00:00)

Today: the basic ideas behind every communication protocol, the ways in which chips and boards talk to each other. Serial and parallel, synchronous and asynchronous, simplex and duplex, baud rate, framing, error detection, and how the wires are arranged. With these ideas, every protocol, from UART and SPI to I2C, CAN and USB, becomes much easier to follow.

### Parallel and serial  (00:28)

In parallel communication, all the bits of a word travel at the same time, each on its own wire. It is simple and fast over short distances, like the data bus inside a computer. Serial communication sends the bits one after another over a single line. It needs far fewer wires and pins, and it works over long cables, which is why almost every link between chips today is serial.

### Skew and crosstalk  (00:53)

Over long or fast links, the wires of a parallel bus never arrive at exactly the same time, and this is called skew. They also pick up noise from each other, which is called crosstalk. A single serial line avoids both, and can simply be run faster.

### Synchronous and asynchronous  (01:11)

The receiver must know when to read each bit. In synchronous communication, a separate clock line goes with the data, and the receiver reads a bit on every clock edge. SPI and I2C work like this. In asynchronous communication, there is no clock wire: both sides agree on the bit rate in advance, and the receiver times the bits by itself, as in a UART.

### The asynchronous frame  (01:35)

So how does an asynchronous receiver find the start of a byte? The line rests high when it is idle. A start bit, always 0, pulls it low and starts the receiver's timer. Then come the data bits, usually 8, with the least significant bit first, an optional parity bit, and finally a stop bit, always 1. This frame is called 8N1 when it has 8 data bits, no parity and 1 stop bit.

### Reading the bits  (02:02)

After the falling edge of the start bit, the receiver waits one and a half bit times, and reads the first data bit in its middle. Then it reads every following bit one bit time later. Because each byte starts again with a new start bit, the two clocks only need to agree within a few percent.

### Baud rate  (02:22)

The speed is given as the baud rate, the number of symbols per second. On a simple serial line, one symbol is one bit, so 9600 baud means 9600 bits per second, and one bit lasts about 104 microseconds. With 8N1, each byte needs 10 bits, so 9600 baud carries at most 960 bytes per second. Common rates are 9600, 19200, 57600 and 115200 baud.

| baud | one bit | max (8N1) |
|---|---|---|
| 9600 | 104 µs | 960 B/s |
| 19200 | 52 µs | 1920 B/s |
| 57600 | 17.4 µs | 5760 B/s |
| 115200 | 8.7 µs | 11520 B/s |

### Simplex, half and full duplex  (02:54)

Next, the direction of the data. Simplex means one direction only, like a GPS module that only sends. Half duplex means both directions, but one at a time, over shared wires, like a walkie-talkie. Full duplex means both directions at the same time, usually over two separate lines, like a phone call.

### Detecting errors  (03:15)

Noise can flip a bit, so many links add a way to detect errors. A parity bit makes the number of ones even or odd, and catches any single flipped bit. Longer messages carry a checksum or a CRC, which also catches most multiple-bit errors. CAN and USB, for example, protect every message with a CRC.

### Point-to-point or a bus  (03:37)

Then there is the question of who is connected to whom. A point-to-point link joins exactly two devices, like a UART. A bus connects many devices to the same wires, so each message needs an address or a select line to say who is meant. Some buses have one master that starts every transfer, while others let any device start, and then they need a way to settle collisions.

### Signal levels  (04:01)

Finally, the voltages. Between chips on a board, simple logic levels are used, for example 0 and 3.3 volts. For longer cables there are standards like RS-232, which uses higher plus and minus voltages. And differential signalling sends each bit on two wires with opposite levels, which makes it very resistant to noise, as in RS-485, CAN and USB.

### Where the protocols fit  (04:27)

Here is how the common protocols fit these ideas. UART is asynchronous, point-to-point and full duplex, SPI is synchronous and full duplex with a select line per device, and I2C is synchronous and half duplex, with addresses on two wires. CAN is a differential bus where any node may send, USB is a differential bus controlled by a host, and 1-Wire uses a single wire for data and even power.

|   | timing | duplex | devices | wires |
|---|---|---|---|---|
| UART | asynchronous | full duplex | point-to-point | 2 (TX, RX) |
| SPI | synchronous | full duplex | select line per device | 4 |
| I2C | synchronous | half duplex | addresses | 2 |
| CAN | asynchronous | half duplex | any node may send | 2, differential |
| USB | asynchronous | half duplex | a host controls | 2 data, differential |
| 1-Wire | asynchronous | half duplex | addresses | 1 (+ ground) |

### Practice  (04:55)

Now try this yourself. Pause the video. A UART runs at 115200 baud with 8N1 framing. How long does one bit last, and how many bytes per second can it carry at most? One bit lasts 1 divided by 115200, about 8.7 microseconds, and with 10 bits per byte, it carries at most 11520 bytes per second.

### Summary  (05:23)

Here is the summary. Serial links send one bit after another, and need fewer wires than parallel ones. Synchronous links send a clock with the data, while asynchronous ones agree on a baud rate and frame each byte with a start and a stop bit. Links can be simplex, half or full duplex, point-to-point or a bus, and use logic, RS-232 or differential levels.

|   | remember |
|---|---|
| serial | one bit after another, few wires |
| synchronous | a clock goes with the data |
| asynchronous | agreed baud rate; start bit, data, stop bit |
| duplex | simplex, half, full |
| wiring | point-to-point or a bus; logic, RS-232, differential |
