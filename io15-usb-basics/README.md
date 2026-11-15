# io15 · USB Explained

USB from the cable to the driver: one host and many devices in a tiered star, the cable with VBUS, D+ and D−, differential half duplex data, low, full, high and SuperSpeed and the 1.5 kOhm speed pull-up, NRZI coding and bit stuffing, packets with SYNC, PID and CRC, token, data and handshake packets, transactions with ACK and NAK, endpoints and the four transfer types, enumeration and descriptors, standard classes (HID, mass storage, CDC, audio), the full speed USB device controller of the LPC1768, and a practice question.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### USB: the universal serial bus  (00:00)

Today: USB, the universal serial bus that connects keyboards, memory sticks, phones and microcontroller boards to a computer. We will see the host and the devices, the D plus and D minus wires, the speeds, how bits are coded with NRZI and bit stuffing, packets and transactions, endpoints and transfer types, and what happens when you plug a device in. Finally, we will see what the LPC1768 offers for USB.

### One host, many devices  (00:29)

USB is built around one host, usually a PC, and many devices. The host controls everything: a device only speaks when the host asks it to. Hubs let one port become many, in a tiered star, and up to 127 devices can share one host controller. This keeps devices simple, and all the hard work stays in the host.

### The USB 2.0 cable  (00:52)

A USB 2.0 cable has four wires: VBUS with 5 volts, ground, and the twisted data pair, D plus and D minus. Data is sent as a differential signal on D plus and D minus, so it resists noise, in one direction at a time: USB 2.0 is half duplex. The host can power small devices through VBUS: 100 milliamps at first, and up to 500 milliamps once the device is configured. USB 3 adds separate, faster wire pairs.

| wire | job |
|---|---|
| VBUS | +5 V |
| D+ | data + |
| D− | data − |
| GND | ground |

### Speeds  (01:25)

USB 2.0 has three speeds: low speed with 1.5 megabits per second, full speed with 12, and high speed with 480. A device announces its speed with a 1.5 kilohm pull-up resistor: on D plus for full speed, and on D minus for low speed. USB 3 SuperSpeed starts at 5 gigabits per second.

| speed | bit rate | example |
|---|---|---|
| low speed | 1.5 Mbit/s | mouse, keyboard |
| full speed | 12 Mbit/s | LPC1768, audio |
| high speed | 480 Mbit/s | disks, cameras |
| SuperSpeed (USB 3) | 5 Gbit/s and more | fast drives |

### NRZI coding and bit stuffing  (01:47)

Bits are not sent as plain levels. USB uses NRZI coding: a 0 is sent as a change of the line state, and a 1 as no change. So long runs of 1s would give no edges, and the receiver could lose the timing. That is why, after six 1s in a row, the sender inserts an extra 0, a stuff bit, which the receiver removes again.

### Packets  (02:12)

Everything on the bus is a packet. Each one starts with a SYNC field, so that the receiver can lock onto the clock, and a packet ID, the PID, that says what kind of packet it is. Token packets like IN, OUT and SETUP say what the host wants, and from which device. Data packets carry the bytes with a CRC, and handshake packets like ACK, NAK and STALL report the result.

### Transactions  (02:39)

A transaction usually has three packets. To send data, the host sends an OUT token, then a data packet, and the device answers ACK. To receive, the host sends an IN token, the device answers with a data packet, and the host sends ACK. If the device has nothing to send yet, it answers NAK, and the host simply asks again later.

### Endpoints and transfer types  (03:02)

Inside a device, data goes to and from endpoints, which are numbered buffers. Endpoint 0 is always there, for control. There are four transfer types: control for setup and commands, bulk for large data like files, interrupt for small regular data like key presses, and isochronous for steady streams like audio. Each type has its own guarantees for timing and error checking.

| type | used for |
|---|---|
| control | setup, commands |
| bulk | large data: files |
| interrupt | small, regular: key presses |
| isochronous | steady streams: audio |

### Enumeration  (03:26)

When you plug a device in, the host notices the pull-up resistor, and resets the device, which then answers at address 0. The host reads the device descriptor, with the vendor ID and the product ID, and gives the device its own address. Then it reads the configuration, interface and endpoint descriptors, chooses a configuration, and loads the right driver. All of this takes a fraction of a second, and it is called enumeration.

### Standard classes  (03:55)

Many devices belong to standard classes, so no special driver is needed. HID is for keyboards, mice and game pads, mass storage for memory sticks, CDC for virtual serial ports, and audio for headsets. A microcontroller that acts as a HID or a CDC device works on any computer right away.

| class | devices |
|---|---|
| HID | keyboards, mice, game pads |
| mass storage | memory sticks |
| CDC | virtual serial (COM) ports |
| audio | headsets, microphones |

### USB on the LPC1768  (04:16)

The LPC1768 has a full speed USB device controller, at 12 megabits per second. Its D plus and D minus pins are P0.29 and P0.30, USB_CONNECT on P2.9 switches the 1.5 kilohm pull-up from software, and VBUS on P1.30 senses the cable. The controller handles the packets, CRCs and handshakes in hardware, and a USB stack in software answers the descriptors and the requests. For simple projects, a USB to serial chip like the CH340 is often the easier way.

| signal | pin |
|---|---|
| USB_D+ | P0.29 |
| USB_D− | P0.30 |
| USB_CONNECT | P2.9 (switches the 1.5 kΩ pull-up) |
| VBUS | P1.30 (senses the cable) |

### Practice  (04:53)

Now try this yourself. Pause the video. A full speed device sends seven 1s in a row. What goes on the wire after bit stuffing, and how long does one bit last? After six 1s, a 0 is inserted, so the sender sends six 1s, a 0, and then the last 1, and at 12 megabits per second, one bit lasts about 83 nanoseconds.

### Summary  (05:18)

Here is the summary. USB has one host that controls everything, and devices that only answer, connected through hubs. D plus and D minus carry differential, half duplex data, coded with NRZI and bit stuffing. Packets carry tokens, data and handshakes, and devices have endpoints and four transfer types. At plug-in, enumeration reads the descriptors, gives an address and loads a driver, and standard classes like HID and CDC need no special driver.

|   | remember |
|---|---|
| host | controls everything; devices only answer; hubs |
| wires | D+, D−: differential, half duplex; NRZI + stuffing |
| packets | tokens, data, handshakes; endpoints, 4 transfer types |
| plug-in | enumeration: descriptors, address, driver; HID, CDC |
