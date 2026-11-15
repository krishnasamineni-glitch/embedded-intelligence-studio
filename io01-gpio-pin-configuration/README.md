# io01 · GPIO and Pin Configuration Explained

GPIO, the general purpose input and output pins, and how to set them up on the LPC1768 (ARM Cortex-M3): pin functions and PINSEL, direction with FIODIR, safe single-pin changes with FIOSET and FIOCLR, reading a whole port with FIOPIN, FIOMASK, pull-up and pull-down resistors with PINMODE, open-drain outputs, current limits and an LED resistor, PCONP, and a complete LED and key example that was compiled and run on an emulated Cortex-M3.

## Files

* [`gpio_demo.c`](gpio_demo.c) – the GPIO examples of the video: an LED on P0.22 that follows a key on P2.10 (LPC1768)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### GPIO and pin configuration  (00:00)

Today: GPIO, the general purpose input and output pins of a microcontroller, and how to set them up on the LPC1768. We will see pin functions, directions, setting and clearing pins, reading inputs, pull-up resistors and open-drain outputs, all with 32-bit register values. This is the base of every interfacing program: LEDs, keys, displays and motors.

### One pin, many jobs  (00:28)

A pin of a microcontroller can do many jobs. The pin P0.2, for example, can be a plain GPIO pin, the transmit line of UART0, or an analog input of the ADC. So before using a pin, we choose its function.

### PINSEL: two bits per pin  (00:44)

On the LPC1768, the PINSEL registers choose the function, with two bits for each pin. PINSEL0 covers P0.0 to P0.15, PINSEL1 covers P0.16 to P0.31, and so on for the other ports. The value 00 always means GPIO, and it is also the value after reset. For P0.2, bits 5 and 4 of PINSEL0 decide, and 01 makes it TXD0.

| register | pins |
|---|---|
| PINSEL0 | P0.0 .. P0.15 |
| PINSEL1 | P0.16 .. P0.31 |
| PINSEL2 | P1.0 .. P1.15 |
| PINSEL3 | P1.16 .. P1.31 |
| PINSEL4 | P2.0 .. P2.15 |

| value | function |
|---|---|
| 00 | GPIO  (reset) |
| 01 | function 1 |
| 10 | function 2 |
| 11 | function 3 |

### PINSEL0 for the UART0 pins  (01:16)

So PINSEL0 equal to 0x00000050 makes P0.2 TXD0 and P0.3 RXD0, the usual UART0 setup. In C, we change only these bits: an AND with the inverted mask clears them, and an OR sets the new value. All the other pins keep their settings.

### FIODIR: input or output  (01:40)

Next, the direction. Each GPIO port has a 32-bit FIODIR register: bit n equal to 1 makes pin n an output, and 0 makes it an input. After reset, all pins are inputs, which is the safe choice. Setting bit 22 of FIODIR0, with an OR of 1 << 22, makes P0.22 an output, and leaves the other 31 pins as they were.

### FIOSET and FIOCLR  (02:07)

To drive outputs, the LPC1768 has two special registers. Writing a 1 to a bit of FIOSET makes that pin high, and writing a 1 to FIOCLR makes it low. Zeros are simply ignored. So writing 1 << 22 to FIOSET0 changes only P0.22, with no read, modify, write sequence, and without touching any other pin.

### FIOPIN: read all 32 pins  (02:36)

FIOPIN reads the present level of all 32 pins of a port at once. To test one input, we mask its bit. If FIOPIN2 AND 1 << 10 is zero, the pin P2.10 is low. And writing to FIOPIN sets all the output pins of the port in one go.

### FIOMASK: protect pins  (02:56)

FIOMASK lets a port ignore some pins. A 1 in FIOMASK protects that pin: writes through FIOPIN, FIOSET and FIOCLR do not change it, and FIOPIN reads it as 0. This is useful when different parts of a program share one port.

### PINMODE: pull-up and pull-down  (03:16)

An input pin that is not connected floats, and reads random values. PINMODE adds an internal resistor: 00 is a pull-up, 11 a pull-down, 10 neither, and 01 is the repeater mode. The reset value is 00, so every pin starts with its pull-up on. A key from the pin to ground then reads 1 when it is released, and 0 when it is pressed.

| PINMODE | resistor |
|---|---|
| 00 | pull-up  (reset value) |
| 01 | repeater mode |
| 10 | neither |
| 11 | pull-down |

### Open-drain outputs  (03:40)

PINMODE_OD makes an output open-drain. The pin can then only pull the line low, and when it lets go, an external resistor pulls the line high. Several devices can share one such line safely, which is exactly how the I2C bus works. Open-drain also lets the line be pulled up to another voltage, within the limits of the pin.

### Small currents only  (04:04)

Each pin can only drive a small current. For an LED, a series resistor limits the current: with 3.3 volts, an LED drop of 2 volts and a resistor of 330 ohms, about 4 milliamps flow. Motors and relays need a driver, such as a transistor or the L293D. And always check the data sheet before connecting a pin to anything above its supply.

### PCONP: power for peripherals  (04:30)

One more step for most peripherals is power. The PCONP register switches the clock of each peripheral on or off, to save power. GPIO is always ready, but the ADC, for example, is off after reset, so its PCONP bit must be set first.

### The complete example  (04:48)

Here is the complete example: an LED on P0.22 and a key on P2.10. PINSEL keeps both as GPIO, FIODIR makes P0.22 an output, and P2.10 stays an input with its pull-up. In the loop, the LED follows the key: FIOSET turns it on while the key is pressed, and FIOCLR turns it off otherwise. In an emulator, a pressed key gave a write of 0x00400000 to FIOSET0, and a released key the same value to FIOCLR0.

| key | write | value |
|---|---|---|
| pressed | FIOSET0 | 0x00400000 |
| released | FIOCLR0 | 0x00400000 |

### Practice  (05:27)

Now try this yourself. Pause the video. Which value makes P0.15 an output, and which register then makes it high? The answers: an OR of 0x00008000 into FIODIR0, and then a write of 0x00008000 to FIOSET0. Because 1 shifted left by 15 is 0x00008000.

### Summary  (05:57)

Here is the summary. PINSEL chooses the function of a pin, and FIODIR its direction. FIOSET and FIOCLR change single pins safely, FIOPIN reads the whole port, and FIOMASK protects pins. PINMODE gives pull-ups and pull-downs, PINMODE_OD open-drain outputs, and PCONP powers the peripherals.

|   | remember |
|---|---|
| PINSEL | function of each pin (00 = GPIO) |
| FIODIR | direction: 1 = output |
| FIOSET  FIOCLR | change single pins safely |
| FIOPIN | read (or write) the whole port |
| FIOMASK | protect pins |
| PINMODE | pull-up, pull-down, neither |
| PINMODE_OD | open-drain outputs |
| PCONP | power for the peripherals |
