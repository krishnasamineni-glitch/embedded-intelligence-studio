# io14 · CAN Bus Explained

CAN, the controller area network: why cars use one bus, CAN_H and CAN_L with 120 ohm ends, controller and transceiver, recessive 1 and dominant 0, identifiers instead of addresses, the standard data frame, bitwise arbitration where the lowest identifier wins (0x123 beats 0x125), the acknowledge slot, stuff bits, CRC and error states, bit timing with time quanta (500 kbit/s from 25 MHz, sample point 70 %), CAN1 of the LPC1768 with CAN1BTR, CAN1MOD, CAN1TFI1, CAN1TID1, CAN1TDA1 and CAN1CMR, the values seen on an emulated Cortex-M3, CAN FD and where CAN is used, and a practice question.

## Files

* [`can_demo.c`](can_demo.c) – CAN1 of the LPC1768 at 500 kbit/s: bit timing and sending one standard frame
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_can.py`](test_can.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_can.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### CAN: the controller area network  (00:00)

Today: CAN, the controller area network, the bus that ties together the electronic units of a car, and of trucks, machines and robots. We will see its two differential wires, dominant and recessive bits, messages with identifiers instead of addresses, the frame, the clever arbitration that never loses a message, error handling, bit timing, and the CAN controller of the LPC1768. The bit timing and the transmit registers were checked on an emulated Cortex-M3.

### Why a bus?  (00:31)

A modern car has dozens of control units: engine, brakes, airbag, dashboard and doors. Wiring every unit to every other one would need kilometres of cable. With CAN, all of them share one twisted pair of wires, and every unit can talk to every other one.

### The bus: CAN_H, CAN_L  (00:49)

The bus is two wires, CAN_H and CAN_L, twisted together, with a 120 ohm resistor at each end. Each node has a CAN controller, which handles the protocol, and a transceiver chip, which drives and reads the two wires. The controller only sees TX and RX, like a UART. The transceiver turns them into the differential signal on the bus.

### Recessive 1, dominant 0  (01:13)

CAN has two bus states. Recessive means logic 1: the transceivers let go, and both wires sit at about 2.5 volts. Dominant means logic 0: CAN_H is pulled up to about 3.5 volts, and CAN_L down to about 1.5 volts. If one node sends dominant while the others send recessive, the bus is dominant: a 0 always wins, just like the wired AND of I2C.

### Identifiers, not addresses  (01:40)

CAN messages have no destination address. Instead, each frame has an identifier, 11 bits in a standard frame or 29 bits in an extended frame, that says what the data is, for example the engine speed. Every node hears every frame, and each one keeps only the identifiers it needs. Any node may start sending when the bus is free, so CAN is a multi-master bus.

### A standard data frame  (02:06)

A standard data frame starts with a dominant start of frame bit, then the 11-bit identifier, the RTR bit, and control bits with the data length code. Then come 0 to 8 data bytes, a 15-bit CRC, an acknowledge slot, and 7 recessive end of frame bits. For example, the identifier 0x123 with the two data bytes 0x0B and 0xB8 can carry an engine speed of 3000 rpm. With its stuff bits, this frame is 62 bits long on the wire.

| field | example |
|---|---|
| identifier | 0x123 |
| DLC | 2 |
| data | 0x0B 0xB8 = 3000 rpm |

### Arbitration  (02:39)

Now the clever part: what if two nodes start at the same moment? Both send their identifiers bit by bit, and each node reads the bus while it sends. As soon as a node sends a recessive 1 but reads a dominant 0, it knows that another node has a higher priority, so it stops sending and becomes a receiver. Here 0x123 and 0x125 first differ at bit 2, so 0x123 wins, and its frame goes through without any damage. So the lower the identifier, the higher the priority, and no time is wasted.

### The acknowledge slot  (03:13)

Every node that received the frame correctly sends a dominant bit in the acknowledge slot. So the sender knows that at least one node got it. If nobody acknowledges, the sender tries again.

### Stuff bits and error handling  (03:26)

CAN has no clock wire, so the receivers resynchronise on the edges. To make sure that edges come often enough, after 5 equal bits the sender inserts one opposite bit, called a stuff bit, and the receivers remove it again. Errors are found by the CRC, by checking the stuff bits and the fixed bits, and by each sender reading back its own bits. A node that sees an error sends an error frame, the message is repeated, and a node that makes too many errors switches itself off the bus.

### Bit timing: 500 kbit/s  (03:57)

Each bit is divided into small time quanta. With the 25 megahertz peripheral clock divided by 5, one quantum is 0.2 microseconds, and 10 quanta make one bit of 2 microseconds, so 500 kilobits per second. The bit has a sync segment of 1 quantum, 6 quanta before the sample point and 3 after it, so the bus is read at 70 percent of the bit. Speeds reach 1 megabit per second over about 40 metres, and slower speeds allow longer cables.

| bit rate | bus length |
|---|---|
| 1 Mbit/s | ≈ 40 m |
| 500 kbit/s | ≈ 100 m |
| 125 kbit/s | ≈ 500 m |

### CAN on the LPC1768  (04:29)

The LPC1768 has two CAN controllers. CAN1 uses P0.0 as RD1 and P0.1 as TD1, and these pins go to an external transceiver, like the TJA1050. CAN1BTR holds the bit timing: BRP minus 1 in bits 9 to 0, then SJW, TSEG1 and TSEG2. It may only be changed in reset mode, which is set by bit 0 of CAN1MOD.

### Setup and sending  (04:58)

The setup powers CAN1 with bit 13 of PCONP, selects RD1 and TD1 in PINSEL0, enters reset mode, writes the bit timing, and returns to normal mode. To send, the program waits until transmit buffer 1 is free, writes the data length into CAN1TFI1, the identifier into CAN1TID1, and the data bytes into CAN1TDA1 and CAN1TDB1. Then it writes 0x21 into CAN1CMR: transmit request, buffer 1. The controller does the rest: arbitration, stuffing, CRC and acknowledge.

### On the emulator  (05:36)

On the emulator, can_btr computed 0x00250004 for 500 kilobits per second: BRP 5, TSEG1 6, TSEG2 3, and a sample point of 70 percent. The setup wrote 0x00000005 into PINSEL0, and set the reset mode around the CAN1BTR write. Sending 3000 rpm wrote 0x00020000 into CAN1TFI1, which is a data length of 2, then 0x00000123 into CAN1TID1, and 0x0000B80B into CAN1TDA1. The first data byte sits in the lowest 8 bits, so 0x0B goes first, and then 0xB8.

| register | write |
|---|---|
| CAN1BTR | 0x00250004 |
| PINSEL0 | 0x00000005 |
| CAN1MOD | 1, then 0 |
| CAN1TFI1 | 0x00020000 |
| CAN1TID1 | 0x00000123 |
| CAN1TDA1 | 0x0000B80B |
| CAN1CMR | 0x00000021 |

### Where CAN is used  (06:18)

CAN is used in every car, in trucks, buses, tractors, industrial machines, robots and medical devices, often with higher layer standards on top. Its newer version, CAN FD, sends up to 64 data bytes per frame, and switches to a faster bit rate for the data part. The ideas stay the same: identifiers, arbitration and strong error checking.

### Practice  (06:42)

Now try this yourself. Pause the video. Two nodes start at the same time, one with the identifier 0x100 and one with 0x0FF. Which one wins the arbitration? Written in 11 bits, 0x100 is 001 0000 0000 and 0x0FF is 000 1111 1111, so they first differ at bit 8, where 0x0FF sends the dominant 0, and wins.

### Summary  (07:13)

Here is the summary. CAN uses two differential wires with 120 ohm ends, and a dominant 0 always overrides a recessive 1. Frames carry identifiers instead of addresses, and every node filters what it needs. When nodes collide, the lowest identifier wins the arbitration without losing a bit. Stuff bits, the CRC, acknowledges and error counters keep the bus reliable, and on the LPC1768, CAN1BTR sets the bit timing and CAN1CMR starts a transmission.

|   | remember |
|---|---|
| bus | CAN_H, CAN_L, 120 Ω ends; dominant 0 beats recessive 1 |
| frames | identifiers, not addresses; nodes filter |
| arbitration | the lowest identifier wins, nothing lost |
| reliability | stuff bits, CRC, ACK, error counters |
| LPC1768 | CAN1BTR: bit timing;  CAN1CMR: send |
