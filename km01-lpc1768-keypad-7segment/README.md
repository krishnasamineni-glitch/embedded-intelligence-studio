# km01 · LPC1768: 3x3 Keypad and 7-Segment Display

Code from the video **LPC1768 Keypad + 7-Segment Display Interfacing | ARM Cortex-M3 Registers Explained**
(PINSEL, FIODIR, FIOSET, FIOCLR, FIOPIN, PINMODE; segment codes; keypad scanning and debounce).

| File | What it does |
|---|---|
| `prog1_7seg.c` | 7-segment counter 0–9, one digit per second (SysTick delay) |
| `prog2_keypad.c` | 3x3 keypad scanning with debounce; the pressed key is shown on the display |
| `prog3_lift.c` | Lift (elevator) floor indicator: press 1–9, the display moves floor by floor, the dot glows while moving |

## Wiring

| Part | LPC1768 pins |
|---|---|
| 7-segment, **common cathode** (common → GND): a b c d e f g dp | P0.4 P0.5 P0.6 P0.7 P0.8 P0.9 P0.10 P0.11 (330 Ω each) |
| Keypad rows R1 R2 R3 | P2.0 P2.1 P2.2 (outputs) |
| Keypad columns C1 C2 C3 | P2.3 P2.4 P2.5 (inputs, internal pull-ups on) |

```
          C1  C2  C3
    R1 [  1   2   3 ]
    R2 [  4   5   6 ]
    R3 [  7   8   9 ]
```

## Segment codes (bit0 = a … bit6 = g, 1 = ON)

| Digit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Code | 0x3F | 0x06 | 0x5B | 0x4F | 0x66 | 0x6D | 0x7D | 0x07 | 0x7F | 0x6F |

For a **common anode** display, invert the codes (`~code`) and connect the common pin to +3.3 V.

## How to build and flash (Keil uVision 5)

1. *Project → New µVision Project*, choose the device **NXP LPC1768**.
2. In *Manage Run-Time Environment* tick **CMSIS → CORE** and **Device → Startup** (this adds the startup
   file and `system_LPC17xx.c`, which sets `SystemCoreClock`).
3. Add **one** of the `.c` files of this folder to *Source Group 1* (each file has its own `main`).
4. *Options for Target → Output*: tick **Create HEX File**. Build with **F7**.
5. Flash the `.hex` file: with Flash Magic over the UART bootloader (ISP), or with your board's debugger
   (ULINK / CMSIS-DAP / J-Link) using **F8**.

If your board uses other pins, change the `#define`s at the top of the file; the comments show the wiring.
