# io05 · Seven-Segment Display & Multiplexing Explained

Seven-segment displays from the LEDs up: segments a to g and the decimal point, common cathode and common anode, building the segment code of a digit in one byte (2 = 0x5B, inverted 0xA4), the segment table, the segment resistor, why four digits need multiplexing, one digit at a time and persistence of vision, refresh timing and brightness, wiring with transistors on the LPC1768, the SysTick setup, the refresh routine and why its order matters, splitting a number into digits, the register writes seen on an emulated Cortex-M3, decoder and driver chips, and a practice question.

## Files

* [`sevenseg_demo.c`](sevenseg_demo.c) – a 4-digit common-cathode 7-segment display, multiplexed (LPC1768)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_sevenseg.py`](test_sevenseg.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_sevenseg.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Seven-segment displays  (00:00)

Today: seven-segment displays, and how one microcontroller drives four digits with only 12 pins. We will build the segment codes, see common cathode and common anode displays, and then multiplex four digits fast enough that the eye sees them all at once. The code runs on an LPC1768, and its register writes were checked on an emulated Cortex-M3.

### Seven segments + a decimal point  (00:26)

A seven-segment digit is just eight LEDs: seven bars, named a to g, and a decimal point. Segment a is the top bar, and the names go clockwise around the digit, b, c, d, e and f, with g in the middle. By turning on the right bars, we can show any digit from 0 to 9, and some letters. Each segment needs its own resistor to limit the current, as with any LED.

### Common cathode and common anode  (00:52)

Inside, the eight LEDs share one pin. In a common cathode display, all the cathodes are joined, so the common pin goes to ground, and a segment lights when its pin is high. In a common anode display, the anodes are joined to the supply, and a segment lights when its pin is low. So the same digit needs opposite bit patterns on the two types.

### One byte per digit  (01:13)

We put the eight segments in one byte: bit 0 is a, bit 1 is b, and so on up to bit 6 for g, and bit 7 for the decimal point. For the digit 2, the segments a, b, d, e and g are on. That is bits 0, 1, 3, 4 and 6, which gives 0x5B for a common cathode display. For a common anode display, we invert every bit and get 0xA4.

### The segment table  (01:38)

Doing this for every digit gives the segment table. 0 is 0x3F, 1 is 0x06, and 8, with all seven bars on, is 0x7F. The program keeps this table in flash, and simply looks up the code of each digit.

### The segment resistor  (01:54)

Each segment is a red LED that drops about 2 volts. From a 3.3 volt pin through a 330 ohm resistor, the current is about 1.3 volts divided by 330 ohms, roughly 4 milliamps. That is safe for the pin and bright enough to see.

### Four digits: 32 pins or 12?  (02:13)

Now four digits. Driving each one separately would need 4 times 8, that is 32 pins. Instead, we connect segment a of all four digits together, segment b together, and so on, and use 8 pins for the segments. Then each digit's common pin gets its own switch, so only 4 more pins are needed: 12 in total.

### One digit at a time  (02:36)

But with shared segment lines, all the lit digits would show the same pattern. So we light only one digit at a time. We put the pattern of the first digit on the segment lines and switch on the first digit, then the second digit with its own pattern, and so on. If we cycle fast enough, the eye merges it into four steady digits: this is called persistence of vision.

### Timing: 2 ms per digit  (03:01)

Here each digit stays on for 2 milliseconds. All four digits take 8 milliseconds, so the whole display is refreshed 125 times per second, which looks completely steady. Below about 50 times per second, it starts to flicker. And since each digit is on only a quarter of the time, it looks dimmer, so the segment current is often chosen a little higher, within the limits of the pins.

### Wiring on the LPC1768  (03:26)

In our circuit, the segments a to g and the decimal point are on P2.0 to P2.7. The digit enables DIG0 to DIG3 are on P0.4 to P0.7. Each one drives a transistor that connects that digit's common cathode to ground. A transistor is needed because the common pin can carry the current of all eight segments, about 32 milliamps, which is too much for one port pin.

### Setup  (03:50)

In the setup, PINSEL makes all twelve pins GPIO, and FIODIR makes them outputs: FIODIR2 gets 0x000000FF and FIODIR0 gets 0x000000F0. All digits start switched off. Then SysTick is loaded with 199999, so that it interrupts every 2 milliseconds at 100 megahertz.

| register | value |
|---|---|
| FIODIR2 | 0x000000FF |
| FIODIR0 | 0x000000F0 |
| FIOCLR0 | 0x000000F0 |
| SYST_RVR | 0x00030D3F |
| SYST_CSR | 0x00000007 |

### display_refresh: the order matters  (04:19)

The SysTick interrupt calls display_refresh, which shows the next digit. The order of the steps matters. First all digits are switched off, then the new segment pattern is written, and only then is the next digit switched on. If we changed the segments while the old digit was still on, a faint shadow of the new pattern would appear on the wrong digit.

### show_number  (04:42)

To show a number, show_number splits it into decimal digits: n modulo 10 gives the last digit, and n divided by 10 removes it. For 1234, the digits array becomes 1, 2, 3, 4. The Cortex-M3 has a hardware divide instruction, so this takes only a few clock cycles.

| n | n % 10 | stored |
|---|---|---|
| 1234 | 4 | digits[3] = 4 |
| 123 | 3 | digits[2] = 3 |
| 12 | 2 | digits[1] = 2 |
| 1 | 1 | digits[0] = 1 |

### On the emulator  (05:00)

On the emulator, after show_number of 1234, four interrupts gave these writes. Each time, FIOCLR0 first wrote 0x000000F0 to switch all digits off, and FIOCLR2 wrote 0x000000FF to clear the segments. Then FIOSET2 wrote the codes 0x06, 0x5B, 0x4F and 0x66, for 1, 2, 3 and 4. And FIOSET0 switched on one digit at a time, with 0x10, 0x20, 0x40 and 0x80.

| interrupt | FIOCLR0 | FIOCLR2 | FIOSET2 | FIOSET0 |
|---|---|---|---|---|
| 1 | 0x000000F0 | 0x000000FF | 0x00000006 | 0x00000010 |
| 2 | 0x000000F0 | 0x000000FF | 0x0000005B | 0x00000020 |
| 3 | 0x000000F0 | 0x000000FF | 0x0000004F | 0x00000040 |
| 4 | 0x000000F0 | 0x000000FF | 0x00000066 | 0x00000080 |

### Chips that help  (05:41)

There are also chips that do part of this work. A BCD to seven-segment decoder, such as the CD4511, turns a 4-bit digit into the segment pattern. And a display driver, such as the MAX7219, does the whole multiplexing by itself, and needs only three wires from the microcontroller. Even so, it is worth knowing how multiplexing works, because the same idea is used in LED matrices and keypads.

### Practice  (06:10)

Now try this yourself. Pause the video. What is the segment code of the letter E, for a common cathode display, and for a common anode display? E uses the segments a, d, e, f and g: bits 0, 3, 4, 5 and 6. That gives 0x79 for common cathode, and inverted, 0x86 for common anode.

### Summary  (06:33)

Here is the summary. A seven-segment digit is eight LEDs, and one byte holds its pattern, with 1 for on in a common cathode display, and 0 for on in a common anode display. Multiplexing shares the segment lines, and lights one digit at a time, here for 2 milliseconds each, which is fast enough for the eye. And the safe order is: digits off, new segments, next digit on.

|   | remember |
|---|---|
| segments | 8 LEDs: a .. g, dp → one byte |
| common cathode | 1 = on  (digit 2 = 0x5B) |
| common anode | 0 = on  (digit 2 = 0xA4) |
| multiplexing | shared segments, one digit at a time, 2 ms each |
| safe order | digits off → new segments → next digit on |
