# mp12 · 8086 Pin Diagram Explained

All 40 pins of the 8086 and its two modes. Power and clock, the multiplexed AD0-AD15 and A16-A19/S3-S6 lines, BHE, RD, NMI, INTR and TEST; the minimum mode pins (M/IO, WR, ALE, INTA, HOLD/HLDA, DT/R, DEN) and a minimum mode system with the 8284, 8282 and 8286; then the maximum mode pins, the S2-S0 status codes decoded by the 8288 bus controller, the queue status, LOCK and request/grant.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.
Signals with a bar on top (R̅D̅) are active low.

### 8086 pins  (00:00)

Today: the pins of the 8086. We will go through all 40 pins, and see the two ways the 8086 can be used: minimum mode, for a small single-processor system, and maximum mode, for bigger systems with a coprocessor.

### 40 pins, two modes  (00:17)

The 8086 comes in a 40-pin package, just like the 8085. But it has more signals than pins. So pin 33, MN/MX, decides the mode. If it is tied high, the 8086 works in minimum mode. If it is tied to ground, it works in maximum mode. Eight pins, 24 to 31, change their meaning with the mode.

### Power and clock  (00:42)

First, power and clock. VCC, 5 volts, is pin 40, and there are two ground pins, 1 and 20. The clock enters on pin 19. It comes from the 8284 clock generator, which also gives the RESET and READY signals, on pins 21 and 22.

### AD0-AD15  (01:02)

The 16 lower address lines share their pins with the data bus: AD0 to AD15, on pins 2 to 16 and pin 39. In the first clock state, T1, they carry the address. In T2, T3 and T4 they carry the data. Just like in the 8085, a latch, triggered by ALE, holds the address.

### A16-A19 / S3-S6  (01:24)

The top four address lines, A16 to A19, are on pins 35 to 38. They also carry status: S3 to S6. S3 and S4 tell which segment register is in use: ES, SS, CS or DS. S5 shows the interrupt flag, and S6 is always 0.

| S4 | S3 | segment |
|---|---|---|
| 0 | 0 | ES |
| 0 | 1 | SS |
| 1 | 0 | CS (or none) |
| 1 | 1 | DS |

### BHE  (01:44)

Pin 34 is BHE, bus high enable, shared with status S7. BHE goes low when data travels on the upper half of the data bus, D8 to D15. Together with A0, it selects the even byte, the odd byte, or both.

| B̅H̅E̅ | A0 | transfer | lines |
|---|---|---|---|
| 0 | 0 | whole word | D0 – D15 |
| 0 | 1 | odd byte | D8 – D15 |
| 1 | 0 | even byte | D0 – D7 |
| 1 | 1 | none | — |

### More common pins  (02:02)

A few more common pins. RD, on pin 32, is the read strobe. NMI on pin 17 is the non-maskable interrupt, and INTR on pin 18 is the maskable interrupt request. TEST, on pin 23, is checked by the WAIT instruction: the processor waits until TEST goes low.

### Minimum mode pins  (02:22)

Now minimum mode. Pin 28 is M/IO: high for memory, low for I/O. Note that this is the opposite of the 8085. WR on pin 29 is the write strobe. ALE on pin 25 latches the address. INTA on pin 24 acknowledges an interrupt. And HOLD and HLDA, on pins 31 and 30, hand the buses over for DMA.

### DT/R and DEN  (02:48)

Two more pins control the data bus buffers. DT/R, on pin 27, sets the direction: high to transmit, low to receive. And DEN, on pin 26, enables the buffers. These go to 8286 bidirectional transceivers.

### A minimum mode system  (03:04)

A minimum mode system is simple. The 8284 gives the clock, reset and ready. Three 8282 latches hold the 20-bit address, using ALE. Two 8286 transceivers buffer the 16-bit data bus, using DEN and DT/R. And the 8086 makes all the control signals itself.

### Maximum mode pins  (03:28)

In maximum mode, the eight pins change. Pins 26 to 28 become the status lines S0, S1 and S2. Pins 24 and 25 become QS0 and QS1, the queue status. Pin 29 becomes LOCK. And pins 30 and 31 become RQ/GT1 and RQ/GT0, request and grant.

### S2 S1 S0 and the 8288  (03:52)

The three status lines tell what the current bus cycle is. For example, 100 is a code fetch, 101 is a memory read, and 110 is a memory write. 111 means passive: no bus cycle. The 8288 bus controller decodes them, and makes the control signals: memory read and write, I/O read and write, interrupt acknowledge, ALE, DEN and DT/R.

| S̅2̅ S̅1̅ S̅0̅ | bus cycle |
|---|---|
| 0 0 0 | interrupt acknowledge |
| 0 0 1 | read I/O port |
| 0 1 0 | write I/O port |
| 0 1 1 | halt |
| 1 0 0 | code access (fetch) |
| 1 0 1 | read memory |
| 1 1 0 | write memory |
| 1 1 1 | passive (no cycle) |

### Queue status  (04:20)

The queue status lines report what happens in the instruction queue. 00: no operation. 01: the first byte of an opcode was taken from the queue. 10: the queue was emptied. And 11: a following byte was taken. A coprocessor like the 8087 watches these lines to follow the instruction stream.

| QS1 QS0 | meaning |
|---|---|
| 0 0 | no operation |
| 0 1 | first byte of an opcode taken from the queue |
| 1 0 | queue emptied |
| 1 1 | a following byte taken from the queue |

### LOCK and request/grant  (04:42)

LOCK goes low during an instruction with the LOCK prefix, so that no other processor can take the bus in the middle of it. And the two request and grant pins let other bus masters, like a coprocessor, borrow the bus. Each pin carries the request, the grant, and the release, as pulses on one line.

### Minimum or maximum?  (05:02)

So which mode should we use? Minimum mode is simpler and cheaper, for a single 8086. Maximum mode needs the 8288, but it supports coprocessors like the 8087, and more than one processor sharing the bus.

|   | minimum mode | maximum mode |
|---|---|---|
| MN/M̅X̅ pin | 1  (+5 V) | 0  (GND) |
| control signals | made by the 8086 | made by the 8288 |
| processors | one 8086 | 8086 + 8087, more masters |
| cost | simple, cheap | needs the 8288 |

### Summary  (05:18)

Here is the summary. MN/MX selects the mode. AD0 to AD15 and A16 to A19 are multiplexed, with ALE. BHE enables the upper byte. In minimum mode the 8086 makes its own control signals. In maximum mode it sends S0 to S2, and the 8288 makes the control signals.

| pins | remember |
|---|---|
| MN/M̅X̅ | selects the mode |
| AD0–AD15,  A16–A19 | multiplexed, latched with ALE |
| B̅H̅E̅ | enables the upper byte D8–D15 |
| minimum mode | the 8086 makes the control signals |
| maximum mode | S̅0̅–S̅2̅  →  8288 makes them |
