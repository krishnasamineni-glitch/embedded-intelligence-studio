# km02 · LPC1768: 16x2 LCD in 8-bit and 4-bit Mode

Code from the video **16x2 LCD Interfacing with LPC1768 | 8-bit and 4-bit Mode Explained**
(HD44780 instruction and data registers, DDRAM addresses, RS/EN timing, the commands you need).

| File | What it does |
|---|---|
| `lcd_8bit.c` | 8-bit mode driver + demo: "Hello, LPC1768" and a seconds counter |
| `lcd_4bit.c` | 4-bit mode driver + the same demo, with only four data lines |

## Wiring

| LCD pin | 8-bit mode | 4-bit mode |
|---|---|---|
| D0 – D3 | P0.15 – P0.18 | not connected |
| D4 – D7 | P0.19 – P0.22 | P0.19 – P0.22 |
| RS (0 = command, 1 = character) | P0.23 | P0.23 |
| EN (latched on the falling edge) | P0.24 | P0.24 |
| RW | GND (write only) | GND |
| VSS / VDD / V0 | GND / +5 V / middle of a 10 kΩ pot (contrast) | same |

## Commands used

| Command | Meaning |
|---|---|
| 0x38 / 0x28 | function set: 2 lines, 5x8 dots, 8-bit / 4-bit |
| 0x0C | display on, cursor off |
| 0x06 | entry mode: move the cursor right |
| 0x01 | clear the display (needs about 2 ms) |
| 0x80 + addr | set the DDRAM address: line 1 starts at 0x00 (0x80), line 2 at 0x40 (0xC0) |

## How to build and flash (Keil uVision 5)

1. *Project → New µVision Project*, choose the device **NXP LPC1768**.
2. In *Manage Run-Time Environment* tick **CMSIS → CORE** and **Device → Startup** (this adds the startup
   file and `system_LPC17xx.c`, which sets `SystemCoreClock`).
3. Add **one** of the `.c` files of this folder to *Source Group 1* (each file has its own `main`).
4. *Options for Target → Output*: tick **Create HEX File**. Build with **F7**.
5. Flash the `.hex` file: with Flash Magic over the UART bootloader (ISP), or with your board's debugger
   (ULINK / CMSIS-DAP / J-Link) using **F8**.

If your board uses other pins, change the `#define`s at the top of the file; the comments show the wiring.
