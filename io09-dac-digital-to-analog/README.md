# io09 · DAC Explained

The digital to analog converter: what a DAC does, the formula Vout = D / 2^n x VREF, binary weighted resistors and the R-2R ladder (1010 gives 0.625 of the reference), resistor string and PWM DACs, the 10-bit DAC of the LPC1768 on P0.26 with the DACR register and the BIAS bit, the code, the values seen on an emulated Cortex-M3 (including a wrap-around bug at 1024 that the emulator caught), a sine wave from a 32-entry table driven by a timer interrupt, smoothing with an RC filter, and a practice question.

## Files

* [`dac_demo.c`](dac_demo.c) – the 10-bit DAC of the LPC1768: a fixed voltage and a sine wave on AOUT (P0.26)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_dac.py`](test_dac.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_dac.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### The DAC: digital to analog  (00:00)

Today: the digital to analog converter, the DAC, the opposite of the ADC. A DAC turns a number from the processor into a voltage, for sound, for waveforms, or for a control level. We will see how a DAC works inside, the R-2R ladder, the 10-bit DAC of the LPC1768 and its register, and how to make a sine wave. The code was checked on an emulated Cortex-M3, and it even caught a small bug.

### ADC and DAC  (00:31)

An ADC measures a voltage and gives a number. A DAC does the reverse: we write a number, and its output pin goes to the matching voltage. Audio players, signal generators and motor controllers all use one.

### The formula  (00:46)

The formula is the ADC formula turned around. The output voltage is the number D divided by 2 to the n, times the reference voltage. The LPC1768 DAC has 10 bits, so D goes from 0 to 1023, and with 3.3 volts, one step is about 3.2 millivolts. Writing 512 gives exactly half, 1.65 volts.

### Idea 1: one resistor per bit  (01:12)

How does a DAC make a voltage from bits? The simplest idea is one resistor per bit, with the values R, 2R, 4R and so on, so that each bit adds a current twice as large as the next one. But for 10 bits, the resistors would range from R to 512 R, and such precise values are hard to make on a chip.

### Idea 2: the R-2R ladder  (01:34)

The R-2R ladder needs only two resistor values, R and 2R. Each bit switches its 2R resistor to the reference or to ground, and the ladder halves the contribution of every bit as it moves along. For the 4-bit number 1010, the output is 8 plus 2, out of 16, times the reference, which is 0.625 of it. More bits simply add more steps to the ladder.

### Other DAC designs  (02:01)

Other designs exist too. A resistor string DAC divides the reference with a chain of equal resistors and picks one tap, and this is what the LPC1768 uses. And as we saw with PWM, a PWM signal through an RC filter also works as a simple DAC.

### The DAC of the LPC1768  (02:20)

The DAC of the LPC1768 has one output, AOUT, on P0.26. It is a 10-bit resistor string DAC with a buffered output, and it needs no power bit in PCONP. Its output can drive only a light load, well below a milliamp, so a speaker or a motor needs an amplifier. The BIAS bit chooses between a faster settling time of 1 microsecond and a lower supply current.

| BIAS | settling | current | max update |
|---|---|---|---|
| 0 | 1 µs | 700 µA | 1 MHz |
| 1 | 2.5 µs | 350 µA | 400 kHz |

### DACR  (02:48)

The DAC has one register, DACR. The 10-bit value goes into bits 15 to 6, and bit 16 is BIAS. So to output the value D, we write D shifted left by 6. For 512, that is 0x00008000.

### The code  (03:08)

The setup selects AOUT for P0.26: PINSEL1 bits 21 and 20 become 10, and PINMODE1 switches off the pull resistors. dac_write masks the value to 10 bits and shifts it into place. dac_value_for_mv converts millivolts into a DAC value, as 1024 times the millivolts divided by 3300. And it limits the result to 1023, for a reason we will see on the emulator.

### On the emulator (and a bug)  (03:39)

On the emulator, the setup wrote 0x00200000 into both PINSEL1 and PINMODE1. A request for 1650 millivolts gave the value 512 and wrote 0x00008000, and 1000 millivolts gave 310, with 0x00004D80, which is 0.999 volts. Then came the surprise: in the first version, 3300 millivolts gave 1024. That does not fit in 10 bits, so the mask turned it into 0, and the output fell to 0 volts instead of the top. With the limit, it writes 1023, which is 0x0000FFC0, or 3.297 volts.

| request | value | DACR | Vout |
|---|---|---|---|
| 1650 mV | 512 | 0x00008000 | 1.650 V |
| 1000 mV | 310 | 0x00004D80 | 0.999 V |
| 3300 mV, first version | 1024 → 0 | 0x00000000 | 0 V ! |
| 3300 mV, with the limit | 1023 | 0x0000FFC0 | 3.297 V |

### A sine wave from a table  (04:26)

A DAC can also draw waveforms. We store one period of a sine in a table of 32 values, from 1 to 1023, centred on 512. A timer interrupt writes the next value into DACR at a fixed rate. For a 1 kilohertz sine with 32 samples per period, that is 32 thousand updates per second.

### On the emulator: 32 samples  (04:48)

On the emulator, 32 calls of dac_next_sample wrote the whole table: 0x00008000 first, then 0x00009900 and 0x0000B100, up to 0x0000FFC0 at the peak. The next call started again with 0x00008000. Plotted, the values form one clean sine period, made of small steps.

| call | DACR | value |
|---|---|---|
| 1 | 0x00008000 | 512 |
| 2 | 0x00009900 | 612 |
| 3 | 0x0000B100 | 708 |
| … | … | … |
| 9 | 0x0000FFC0 | 1023 |
| 33 | 0x00008000 | 512 |

### Smoothing the steps  (05:18)

Those steps are the price of a digital source. A simple low pass filter, a resistor and a capacitor after the output, smooths them into a nearly perfect sine. The more samples per period, the smaller the steps, and the easier the filtering.

### Practice  (05:34)

Now try this yourself. Pause the video. Which value must we write into DACR to get 1 volt, and what voltage do we really get? 1 volt times 1024 divided by 3.3 gives 310, so DACR gets 310 shifted left by 6, which is 0x00004D80. And the output is 0.999 volts.

### Summary  (05:59)

Here is the summary. A DAC turns a number into a voltage: D divided by 2 to the n, times the reference. Inside, an R-2R ladder or a resistor string makes the steps. On the LPC1768, select AOUT on P0.26, write the 10-bit value shifted left by 6 into DACR, and keep the value at or below 1023. For waveforms, write a table at a fixed rate, and smooth the steps with a filter.

|   | remember |
|---|---|
| DAC | Vout = D / 2ⁿ × VREF |
| inside | R-2R ladder or resistor string |
| LPC1768 | AOUT on P0.26, DACR = D << 6 |
| the limit | D ≤ 1023, or it wraps to 0 |
| waveforms | a table at a fixed rate + an RC filter |
