# io11 · UART Explained

The UART from the wires to the registers: crossed TX and RX with a common ground, the 8N1 frame of the letter A, inside a UART (shift registers, FIFOs, 16x sampling), making the baud rate from a 25 MHz clock (divisor 163 for 9600 baud), the fractional divider for 115200 baud, the UART0 registers U0LCR, DLAB, U0DLL, U0DLM, U0THR, U0RBR and U0LSR, the setup and the polling code, what an emulated Cortex-M3 with a model of UART0 really sent (Hello), RS-232 levels and the MAX3232, the RS-485 differential bus, USB to serial adapters, common mistakes, and a practice question.

## Files

* [`uart_demo.c`](uart_demo.c) – UART0 of the LPC1768: 9600 baud 8N1 on P0.2 (TXD0) and P0.3 (RXD0)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_uart.py`](test_uart.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_uart.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### UART, RS-232 and RS-485  (00:00)

Today: the UART, the simplest and most common serial port, and the RS-232 and RS-485 standards that carry it over longer cables. We will see the two wires and the frame, how the baud rate is made from the clock, the UART0 registers of the LPC1768 with real values, sending and receiving by polling, and the wiring mistakes everyone makes once. The code was run on an emulated Cortex-M3 with a model of the UART, and it really sent Hello.

### Two wires and a ground  (00:35)

A UART link needs just two signal wires and a ground. The TX pin of one side goes to the RX pin of the other, and the other way round. There is no clock wire: both sides must be set to the same baud rate and the same frame format. Each side can send at any time, so the link is full duplex.

### The frame  (00:55)

Every byte is sent in a frame: the line idles high, a start bit pulls it low, then 8 data bits follow, least significant bit first, and a stop bit brings it high again. This is the 8N1 format, the most common one. Here is the letter A, 0x41, as it appears on the TX wire.

### Inside a UART  (01:16)

Inside, a UART has a transmitter and a receiver. The transmitter takes a byte from its holding register and shifts it out bit by bit. The receiver watches RX, finds the start bit, samples every bit in its middle, and puts the byte into a receive register. A small FIFO on each side stores a few bytes, so the processor does not have to react to every single bit.

### Making the baud rate  (01:39)

The bit timing comes from the peripheral clock. The UART divides it by 16 times a divisor, because it samples each bit 16 times. With a 25 megahertz clock and 9600 baud, the divisor is 25 million divided by 16 times 9600, about 162.8, so we use 163. That gives 9586 baud, only 0.15 percent too slow, which is fine.

### 115200: the fractional divider  (02:09)

At 115200 baud it is harder. The nearest divisor, 14, gives 111607 baud, more than 3 percent off, which is too much. The LPC1768 has a fractional divider that multiplies the divisor by 1 plus DIVADDVAL over MULVAL. With a divisor of 9 and a factor of 1.5, we get 115741 baud, only 0.47 percent off.

| divisor | fraction | baud | error |
|---|---|---|---|
| 14 | — | 111607 | −3.1 % |
| 9 | × 1.5 | 115741 | +0.47 % |

### UART0 registers  (02:40)

UART0 is controlled by a few registers. U0LCR sets the frame format, and its bit 7, DLAB, switches two addresses over to the divisor registers U0DLL and U0DLM. U0THR is where we write a byte to send, and U0RBR is where we read a received byte. U0LSR, the line status register, tells us in bit 0 whether a byte has arrived, and in bit 5 whether there is room to send.

| register | job |
|---|---|
| U0LCR | frame format; bit 7 = DLAB |
| U0DLL, U0DLM | divisor (when DLAB = 1) |
| U0THR | write: a byte to send |
| U0RBR | read: a received byte |
| U0LSR | bit 0 RDR: data ready;  bit 5 THRE: room to send |

### Setup: 9600 baud, 8N1  (03:15)

Here is the setup for 9600 baud. PINSEL0 gives P0.2 and P0.3 their TXD0 and RXD0 functions, with the value 0x50. U0LCR gets 0x83: 8 data bits, no parity, 1 stop bit, and DLAB set, so that we can write 163 into U0DLL and 0 into U0DLM. Then U0LCR gets 0x03 to clear DLAB, and U0FCR gets 0x07 to switch on and clear the FIFOs.

### Polling  (03:53)

To send a character, uart0_putc waits until bit 5 of U0LSR, called THRE, shows that the transmit register is empty, and then writes the byte to U0THR. To receive, uart0_getc waits until bit 0, called RDR, shows that a byte is ready, and then reads U0RBR. Waiting in a loop like this is called polling. It is simple, but the processor does nothing else while it waits, so larger programs use the UART interrupt instead.

### On the emulator  (04:27)

On the emulator, a model of UART0 recorded every register write. The setup wrote 0x00000050, then 0x00000083, 0x000000A3, which is 163, then 0x00000000, 0x00000003 and 0x00000007, exactly as planned. Then the transmitter received 0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x0D and 0x0A, which is Hello followed by a new line. And the echo routine turned the received text abc into ABC, one character at a time.

| register | write |
|---|---|
| PINSEL0 | 0x00000050 |
| U0LCR | 0x00000083 |
| U0DLL | 0x000000A3 |
| U0DLM | 0x00000000 |
| U0LCR | 0x00000003 |
| U0FCR | 0x00000007 |

### RS-232  (05:00)

A UART pin uses logic levels, 0 and 3.3 volts, which only reach from a few centimetres to about a metre. RS-232 sends the same frames with higher voltages, about plus and minus 5 to 12 volts, and with the logic inverted: a negative voltage means 1. A level shifter chip like the MAX3232 converts between the two. RS-232 reaches about 15 metres, and you find it on the 9-pin connectors of older PCs and on industrial equipment.

### RS-485  (05:32)

For long distances and many devices, there is RS-485. It sends each bit as the difference between two wires, A and B, so noise that hits both wires cancels out. It reaches about 1200 metres, and up to 32 devices can share one pair, with a 120 ohm resistor at each end of the cable. Because the pair is shared, only one device sends at a time, and the program switches its transceiver, like a MAX485, between sending and receiving.

### Talking to a PC  (06:04)

To talk to a PC, a USB to serial adapter is used, with chips like the CH340 or the FT232. On the PC, a terminal program opens the port with the same settings: 9600 baud, 8 data bits, no parity, 1 stop bit. Many LPC1768 boards already have such an adapter on board.

### Common mistakes  (06:28)

A few mistakes cause most UART problems. TX connected to TX instead of RX: nothing arrives. Different baud rates on the two sides: you see garbage characters. And a missing common ground, or a 5 volt signal on a 3.3 volt pin, can give errors or even damage.

### Practice  (06:48)

Now try this yourself. Pause the video. With a 25 megahertz peripheral clock, which divisor gives 19200 baud, and how large is the error? 25 million divided by 16 times 19200 is about 81.4, so we use 81. That gives 19290 baud, an error of 0.47 percent, which is fine.

### Summary  (07:14)

Here is the summary. A UART link is two crossed wires plus ground, full duplex, with an agreed baud rate and frame, usually 8N1. On the LPC1768, the baud rate is PCLK divided by 16 times the divisor, with the fractional divider for exact rates like 115200. Set DLAB in U0LCR to write the divisor, then wait for THRE to send, and for RDR to receive. RS-232 and RS-485 carry the same frames over longer cables.

|   | remember |
|---|---|
| wiring | TX → RX, RX ← TX, common ground; full duplex |
| frame | agreed baud rate, usually 8N1 |
| baud | PCLK / (16 × divisor), × fraction for 115200 |
| registers | DLAB in U0LCR, then THRE to send, RDR to receive |
| cables | RS-232 (±12 V, 15 m), RS-485 (A − B, 1200 m, 32 nodes) |
