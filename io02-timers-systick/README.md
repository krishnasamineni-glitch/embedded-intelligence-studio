# io02 · Timers, Delays and SysTick Explained

How a microcontroller keeps exact time: why software delay loops are unreliable, the timer counter and its prescaler, match registers and MCR, a 1 millisecond Timer0 interrupt on the LPC1768, an exact delay_ms, capture inputs for measuring pulses, match outputs for a 1 kHz square wave without CPU time, and the SysTick timer of the Cortex-M3 with SysTick_Config. The register values were checked on an emulated Cortex-M3.

## Files

* [`timer_demo.c`](timer_demo.c) – the timer examples of the video (LPC1768, CCLK = 100 MHz, PCLK = 25 MHz)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Timers, delays and SysTick  (00:00)

Today: timers, the hardware counters that measure time in a microcontroller. We will build an exact 1 millisecond tick on the LPC1768, measure a pulse, make a square wave without the CPU, and use the SysTick timer of the Cortex-M3. As always, the register values were checked by running the code on an emulated Cortex-M3.

### Why not just a loop?  (00:24)

The simplest delay is a loop that counts. But its length depends on the clock frequency, on the compiler and its optimization level, and on every interrupt that steals time. Change one of them, and the delay changes too. A hardware timer counts real clock cycles, so its time is exact.

### A counter with a prescaler  (00:42)

A timer is a 32-bit counter, called TC, with a prescaler in front of it. On the LPC1768, the timers run from PCLK, which is 25 megahertz when the processor runs at 100 megahertz. The prescaler counts up to the value in PR, and only then does TC go up by one. With PR equal to 24, TC counts once every 25 cycles: exactly once per microsecond.

### Match registers  (01:11)

Match registers compare TC with a value. When TC reaches MR0, the timer can raise an interrupt, reset TC, or stop, as chosen in MCR. With reset on match, TC counts from 0 up to MR0 and starts again. So a period of 1000 ticks needs MR0 equal to 999.

| MCR |   | on match |
|---|---|---|
| bit 0 | MR0I | interrupt |
| bit 1 | MR0R | reset TC |
| bit 2 | MR0S | stop |

### A 1 ms tick with Timer0  (01:33)

Here is a 1 millisecond tick with Timer0. PR is 24 for microseconds, MR0 is 999, and MCR is 3, which means interrupt and reset on MR0. NVIC_ISER0 equal to 2 enables the TIMER0 interrupt, number 1, and TCR equal to 1 starts the timer.

| register | address | value |
|---|---|---|
| T0TCR | 0x40004004 | 2 |
| T0PR | 0x4000400C | 24 |
| T0MR0 | 0x40004018 | 999 |
| T0MCR | 0x40004014 | 3 |
| NVIC_ISER0 | 0xE000E100 | 0x2 |
| T0TCR | 0x40004004 | 1 |

### The interrupt handler  (01:56)

Every millisecond the interrupt handler runs. It writes 1 to IR to clear the match flag, and adds one to the ms counter. If the flag was not cleared, the handler would run again at once.

### An exact delay  (02:09)

Now a delay is easy and exact. delay_ms remembers the counter, and waits until n milliseconds have passed. And the subtraction even works when the 32-bit counter wraps around after 49 days.

### Capture: measuring a pulse  (02:23)

Timers can also measure time from outside. A capture input copies TC into a capture register, CR0, at the moment an edge arrives on its pin. If the rising edge is captured at 1200 and the falling edge at 1700, the pulse was 500 microseconds long. This is how we measure the echo of an ultrasonic sensor, or the speed of a motor.

### Match outputs: a square wave  (02:47)

Match outputs work the other way round. With EMR, a match can set, clear or toggle a pin by itself. With MR0 equal to 499 and toggle on match, the pin MAT0.0 changes every 500 microseconds, a 1 kilohertz square wave, with no CPU time at all.

| EMC0 | on match |
|---|---|
| 00 | do nothing |
| 01 | clear the pin |
| 10 | set the pin |
| 11 | toggle the pin |

### SysTick: the timer in the core  (03:08)

Every Cortex-M processor also has a small timer inside the core: SysTick. It is a 24-bit counter that counts down from the value in LOAD to zero, then reloads and starts again. At each zero it sets the COUNTFLAG bit, and it can raise the SysTick exception. Because it is part of the core, the same code works on every Cortex-M chip.

### SysTick: 1 ms at 100 MHz  (03:29)

For a 1 millisecond tick at 100 megahertz, LOAD is 100000 minus 1, which is 99999, or 0x0001869F. CTRL equal to 7 enables the counter and its interrupt, and selects the processor clock. The largest LOAD value is 0x00FFFFFF, so at 100 megahertz one SysTick period can be at most about 167 milliseconds.

| CTRL |   |   |
|---|---|---|
| bit 0 | ENABLE | 1 |
| bit 1 | TICKINT | 1: exception |
| bit 2 | CLKSOURCE | 1: processor clock |

### CMSIS SysTick_Config  (03:54)

CMSIS does all of this in one call: SysTick_Config with SystemCoreClock divided by 1000. It returns 0 when the value fits into 24 bits. The tick then counts milliseconds in SysTick_Handler.

### Which timer for which job?  (04:09)

So which one should we use? SysTick is perfect for a regular tick, for delays and for an operating system. The peripheral timers add capture inputs and match outputs, and the LPC1768 has four of them, plus a separate PWM unit.

### Practice  (04:25)

Now try this yourself. Pause the video. PCLK is 25 megahertz, and we want TC to count in steps of 10 microseconds. Which value goes into PR? The answer: 249, because 250 cycles of 25 megahertz take exactly 10 microseconds.

### Summary  (04:45)

Here is the summary. A timer counts PCLK cycles through a prescaler: one tick is PR plus 1 divided by PCLK. Match registers give interrupts, resets and output pins, and capture registers measure input edges. SysTick, inside every Cortex-M core, gives a simple and portable tick.

|   | remember |
|---|---|
| tick | (PR + 1) / PCLK |
| MR0 + MCR | interrupt, reset, stop on match |
| period | N ticks: MR0 = N − 1 |
| EMR | set, clear or toggle a pin on match |
| capture | TC copied into CR at an edge |
| SysTick | 24-bit, LOAD = clock / rate − 1 |
