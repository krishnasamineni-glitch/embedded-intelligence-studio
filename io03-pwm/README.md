# io03 · PWM Explained

PWM, pulse width modulation, from the idea to the registers: period, pulse width and duty cycle, average voltage, LED brightness, motor speed, servo angle and a simple RC analog output, choosing the frequency, the PWM1 unit of the LPC1768 with MR0 for the period and MR1 for the pulse width, a complete 1 kHz / 25 % setup on P2.0, glitch-free changes with LER, a 50 Hz servo signal, and double-edge PWM. The register values were checked on an emulated Cortex-M3.

## Files

* [`pwm_demo.c`](pwm_demo.c) – the PWM examples of the video: PWM1.1 on P2.0, 1 kHz, 25 % duty (LPC1768, PCLK = 25 MHz)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### PWM: pulse width modulation  (00:00)

Today: PWM, pulse width modulation. With PWM, a digital pin that can only be high or low controls the brightness of an LED, the speed of a motor and the angle of a servo. We will see the idea, then set up the PWM unit of the LPC1768 with real register values, checked on an emulated Cortex-M3.

### Period, pulse width, duty cycle  (00:26)

A PWM signal switches a pin on and off at a fixed rate. The time of one cycle is the period, and the part of it that is high is the pulse width. The duty cycle is the pulse width divided by the period. The load does not follow every switch: it sees the average.

### Duty cycle and average voltage  (00:44)

With a 3.3 volt pin, a duty cycle of 25 percent gives an average of 0.825 volts, 50 percent gives 1.65 volts, and 75 percent gives about 2.5 volts. So by changing only the timing, we get any average value between 0 and 3.3 volts.

### Where PWM is used  (01:03)

This is why PWM is everywhere. The eye averages a fast blinking LED into a steady brightness. A motor, driven through a transistor or an H-bridge, runs at a speed set by the duty cycle. A hobby servo reads the width of each pulse as an angle. And with a resistor and a capacitor, PWM even becomes a simple analog output.

### Choosing the frequency  (01:26)

The frequency must suit the load. For LEDs, a few hundred hertz or more avoids visible flicker, motors usually run at several kilohertz, and servos expect exactly 50 hertz, one pulse every 20 milliseconds.

| load | frequency | why |
|---|---|---|
| LED | a few hundred Hz or more | no visible flicker |
| motor | several kHz | smooth, often quiet |
| servo | 50 Hz | one pulse every 20 ms |

### PWM1 on the LPC1768  (01:42)

The LPC1768 has a PWM unit called PWM1. It is a timer with its own TC, prescaler and seven match registers, MR0 to MR6, and six outputs, PWM1.1 to PWM1.6. MR0 sets the period for all outputs. In single-edge mode, each output goes high at the start of the period, and goes low when TC reaches its own match register.

### MR0 = period, MR1 = pulse width  (02:10)

So for PWM1.1, MR0 sets the period, and MR1 sets the pulse width. The duty cycle is simply MR1 divided by MR0. All six outputs share the same period, but each can have its own duty cycle.

### 1 kHz, 25 % on P2.0  (02:27)

Here is a 1 kilohertz signal with 25 percent duty on P2.0. PINSEL4 selects PWM1.1 for P2.0, and PR equal to 24 gives ticks of 1 microsecond. MR0 equal to 1000 gives a period of 1 millisecond, and MR1 equal to 250 a pulse of 250 microseconds. MCR resets TC on MR0, LER latches the new values, PCR enables the output, and TCR equal to 9 starts the counter in PWM mode.

| register | value |
|---|---|
| PWM1PR | 24 |
| PWM1MR0 | 1000 |
| PWM1MR1 | 250 |
| PWM1MCR | 2 |
| PWM1LER | 3 |
| PWM1PCR | 0x200 |
| PWM1TCR | 9 |

### LER: glitch-free changes  (03:02)

The latch register, LER, protects the waveform. A new match value is not used at once, but only after its LER bit is set, and then from the start of the next period. So changing MR1 to 750, and writing 1 << 1 to LER, switches to 75 percent duty without a single broken pulse.

### A servo: 50 Hz  (03:24)

A servo needs a period of 20 milliseconds, so MR0 becomes 20000. The pulse width then sets the angle: about 1 millisecond for one end, 1.5 milliseconds for the middle, and about 2 milliseconds for the other end. So MR1 equal to 1500 puts the servo in its middle position.

### Double-edge PWM  (03:44)

The PWM unit can also work in double-edge mode, chosen with the PWMSEL bits in PCR. Then two match registers set both edges of a pulse, so pulses can be placed anywhere in the period. This is used, for example, to center the pulses of several outputs in motor control.

### Practice  (04:03)

Now try this yourself. Pause the video. MR0 is 1000, and we want a duty cycle of 40 percent. Which value goes into MR1, and what average voltage do we get? The answer: MR1 equal to 400, and an average of 1.32 volts.

### Summary  (04:24)

Here is the summary. PWM controls an average by changing the pulse width, at a fixed frequency that suits the load. On the LPC1768, MR0 sets the period, MR1 to MR6 set the pulse widths, and the duty cycle is MRn divided by MR0. LER makes changes take effect cleanly at the next period, and double-edge mode sets both edges of each pulse.

|   | remember |
|---|---|
| duty cycle | pulse width / period → average |
| frequency | suits the load: LED, motor, servo 50 Hz |
| MR0 | period (all outputs) |
| MR1 .. MR6 | pulse widths: duty = MRn / MR0 |
| LER | new values at the next period |
| PWMSEL | double edge: both edges set |
