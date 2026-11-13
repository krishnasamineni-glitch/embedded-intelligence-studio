# km03 · LPC1768: Bipolar Stepper Motor with the L293D (Full Step and Half Step)

Code from the video **Stepper Motor with LPC1768 and L293D | Full Step and Half Step Explained**
(inside a bipolar stepper, the H-bridge, the L293D, step sequences, FIOMASK, speed and angle).

| File | What it does |
|---|---|
| `stepper_l293d.c` | Full step (200 steps per turn) and half step (400 steps per turn) with an L293D |

## Wiring

| Connection | To |
|---|---|
| L293D IN1, IN2, IN3, IN4 | P2.0, P2.1, P2.2, P2.3 |
| L293D EN1 (pin 1), EN2 (pin 9) | +5 V (both bridges always on) |
| L293D VCC1 (pin 16) | +5 V logic supply |
| L293D VCC2 (pin 8) | motor supply (for example 12 V) |
| Coil A | OUT1 (pin 3), OUT2 (pin 6) |
| Coil B | OUT3 (pin 11), OUT4 (pin 14) |
| L293D GND (pins 4, 5, 12, 13) | board GND (common ground) |

## Step sequences (bit0 = IN1 (A+), bit1 = IN2 (A−), bit2 = IN3 (B+), bit3 = IN4 (B−))

| Mode | Sequence | Steps per turn (1.8° motor) |
|---|---|---|
| Full step | 0x5, 0x6, 0xA, 0x9 | 200 |
| Half step | 0x1, 0x5, 0x4, 0x6, 0x2, 0xA, 0x8, 0x9 (one coil, two coils, …) | 400 |

## How to build and flash (Keil uVision 5)

1. *Project → New µVision Project*, choose the device **NXP LPC1768**.
2. In *Manage Run-Time Environment* tick **CMSIS → CORE** and **Device → Startup** (this adds the startup
   file and `system_LPC17xx.c`, which sets `SystemCoreClock`).
3. Add **one** of the `.c` files of this folder to *Source Group 1* (each file has its own `main`).
4. *Options for Target → Output*: tick **Create HEX File**. Build with **F7**.
5. Flash the `.hex` file: with Flash Magic over the UART bootloader (ISP), or with your board's debugger
   (ULINK / CMSIS-DAP / J-Link) using **F8**.

If your board uses other pins, change the `#define`s at the top of the file; the comments show the wiring.
