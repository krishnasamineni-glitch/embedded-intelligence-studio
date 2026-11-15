# io08 · ADC Explained

The analog to digital converter from the idea to the registers: analog and digital, resolution and the LSB (12 bits, 0.8 mV), the formula N = Vin / VREF x 4096, quantization error, sampling and the Nyquist rule, aliasing, sample and hold, how a successive approximation (SAR) ADC finds 2482 for 2 V bit by bit, flash, sigma delta and dual slope ADCs, the 12-bit ADC of the LPC1768 with PCONP, PINSEL1, PINMODE1, AD0CR and AD0GDR, the read code, the values seen on an emulated Cortex-M3, averaging noisy readings, an LM35 example, and a practice question.

## Files

* [`adc_demo.c`](adc_demo.c) – reading a voltage with the 12-bit ADC of the LPC1768 (channel AD0.0 on P0.23)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_adc.py`](test_adc.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_adc.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### The ADC: analog to digital  (00:00)

Today: the analog to digital converter, the ADC. The real world is analog: temperature, light and the position of a knob all become voltages, and a processor only understands numbers. We will see how an ADC turns a voltage into a number, what resolution and sampling mean, how a successive approximation ADC works, and how to read a voltage with the 12-bit ADC of the LPC1768. The code was checked on an emulated Cortex-M3 with a model of the ADC.

### Analog and digital  (00:35)

An analog signal can take any value, for example any voltage between 0 and 3.3 volts. A digital value has only a fixed number of steps. The ADC compares the input voltage with a reference voltage, and gives the number of the step it falls into.

### Resolution  (00:52)

The number of bits sets the resolution. An n-bit ADC has 2 to the power n steps, so the 12-bit ADC of the LPC1768 gives numbers from 0 to 4095. With a 3.3 volt reference, one step, called one LSB, is 3.3 volts divided by 4096, about 0.8 millivolts. A 10-bit ADC would have only 1024 steps, each about 3.2 millivolts.

### From volts to a number  (01:22)

The conversion is a simple ratio. The result N is the input voltage divided by the reference, times 4096, rounded down. For 2 volts, that is 2 divided by 3.3, times 4096, which gives 2482. And back again: the voltage is N times 3.3 divided by 4096.

### Quantization error  (01:44)

Because the result is a whole number, every reading has a small error of up to one step. This is called the quantization error, and more bits make it smaller. Noise on the input adds a few more steps of uncertainty, which is why readings are often averaged.

### Sampling and aliasing  (02:00)

An ADC does not watch the signal all the time: it takes samples at a fixed rate. To capture a signal correctly, the sampling rate must be more than twice its highest frequency. This is the Nyquist rule. If we sample too slowly, a fast signal appears as a false slow one, and this is called aliasing.

### Sample and hold  (02:20)

During a conversion, the input must not change. So the ADC first charges a small capacitor to the input voltage, then disconnects it, and converts the held voltage. This is the sample and hold circuit.

### Successive approximation (SAR)  (02:33)

The LPC1768 uses a successive approximation ADC, or SAR. It works like a binary search. First it tries the middle value, 2048, and a comparator tells whether the input is above or below it. If it is above, the top bit stays 1, if it is below, the bit becomes 0, and then the next bit is tried in the same way. After 12 such steps, all 12 bits are known.

### Other kinds of ADCs  (03:01)

There are other kinds of ADCs too. A flash ADC uses one comparator per step, and is extremely fast, but large. A sigma delta ADC is slow but very precise, and dual slope ADCs are found in digital multimeters.

### The ADC of the LPC1768  (03:19)

Now the LPC1768. It has one 12-bit SAR ADC with 8 input channels, AD0.0 to AD0.7, on fixed pins, and AD0.0 is on P0.23. The ADC clock must be at most 13 megahertz, and one conversion takes 65 clocks. So it can do up to about 200 thousand conversions per second.

| channel | pin |
|---|---|
| AD0.0 | P0.23 |
| AD0.1 | P0.24 |
| AD0.2 | P0.25 |
| AD0.3 | P0.26 |
| AD0.4 | P1.30 |
| AD0.5 | P1.31 |
| AD0.6 | P0.3 |
| AD0.7 | P0.2 |

### Setup: four steps  (03:47)

Four things must be set up. PCONP bit 12 powers the ADC, which is off after reset. PINSEL1 bits 15 and 14 select the AD0.0 function for P0.23, and PINMODE1 switches off its pull-up resistor, so that it does not disturb the voltage. AD0CR selects the channel, divides the clock, and switches the converter on.

### AD0CR  (04:12)

In AD0CR, bits 7 to 0 select the channel, bits 15 to 8 hold CLKDIV, and bit 21 is PDN, which switches the ADC on. With CLKDIV equal to 1, the 25 megahertz peripheral clock is divided by 2, which gives 12.5 megahertz. Channel 0, CLKDIV 1 and PDN give the value 0x00200101. Writing 001 into the START field, bits 26 to 24, starts a conversion.

### Reading the ADC  (04:44)

Here is the reading code. adc_read sets START, and then waits for the DONE bit, bit 31 of AD0GDR. The result sits in bits 15 to 4, so we shift right by 4 and keep 12 bits. Finally, adc_millivolts multiplies by 3300 and divides by 4096.

### On the emulator  (05:05)

On the emulator, the setup set bit 12 of PCONP, and wrote 0x00004000 into PINSEL1, 0x00008000 into PINMODE1, and 0x00200101 into AD0CR. With 2 volts at the input, adc_read wrote 0x01200101 to start, and the ADC model returned 0x80009B20 in AD0GDR. That is DONE set and 2482 in the result field, which adc_millivolts turned into 1999 millivolts, because integer division rounds down. With 1.65 volts, the result was exactly 2048.

| register | value |
|---|---|
| PCONP | bit 12 set: 0x042897DE |
| PINSEL1 | 0x00004000 |
| PINMODE1 | 0x00008000 |
| AD0CR | 0x00200101 |
| AD0CR (start) | 0x01200101 |
| AD0GDR (read) | 0x80009B20 |

### Noise and averaging  (05:51)

With a little noise on a 1 volt input, single readings jumped between 1234 and 1248. The average of 16 readings stayed within 2 steps of the ideal value, 1241. Averaging trades speed for a cleaner result.

### Example: LM35  (06:08)

A real example: the LM35 temperature sensor gives 10 millivolts per degree Celsius. At 25 degrees it gives 250 millivolts, and the ADC reads 310. One step is 0.8 millivolts, so the ADC resolves less than a tenth of a degree.

### Practice  (06:27)

Now try this yourself. Pause the video. The 12-bit ADC with a 3.3 volt reference reads 1024. What is the input voltage, and which reading do you expect for 3 volts? The answers: 1024 times 3.3 divided by 4096 is 0.825 volts, and 3 divided by 3.3, times 4096, gives 3723.

### Summary  (06:54)

Here is the summary. An n-bit ADC divides the reference into 2 to the n steps, and for 12 bits, N is the input divided by the reference, times 4096. Sample more than twice as fast as the highest frequency, or aliasing appears. On the LPC1768: power the ADC in PCONP, select the pin in PINSEL, set AD0CR, start, wait for DONE, and take bits 15 to 4.

|   | remember |
|---|---|
| resolution | n bits: 2ⁿ steps, 1 LSB = VREF / 2ⁿ |
| formula | N = Vin / VREF × 4096 (12 bits) |
| sampling | more than 2 × the highest frequency |
| SAR | a binary search, one bit per step |
| LPC1768 | PCONP, PINSEL, AD0CR, START, DONE, bits 15:4 |
