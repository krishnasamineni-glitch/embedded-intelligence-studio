# Embedded Intelligence Studio: code for the videos

Programs and tools used in the videos of the YouTube channel **Embedded Intelligence Studio**.
One folder per video: open the folder of the video you watched.

## ARM Cortex-M3 (LPC1768), Keil C

| Video | Folder |
|---|---|
| km01 · 3x3 keypad and 7-segment display (+ lift floor indicator) | [`km01-lpc1768-keypad-7segment`](km01-lpc1768-keypad-7segment) |
| km02 · 16x2 LCD, 8-bit and 4-bit mode | [`km02-lpc1768-lcd-16x2`](km02-lpc1768-lcd-16x2) |
| km03 · Bipolar stepper motor with the L293D | [`km03-lpc1768-stepper-motor`](km03-lpc1768-stepper-motor) |

## 8085 microprocessor (assembly)

| Video | Folder |
|---|---|
| mp05 · Data transfer instructions: swap program | [`mp05-8085-data-transfer`](mp05-8085-data-transfer) |
| mp06 · Arithmetic instructions: addition with carry, 16-bit addition | [`mp06-8085-arithmetic`](mp06-8085-arithmetic) |
| mp07 · Logical and rotate instructions: nibble program | [`mp07-8085-logical-rotate`](mp07-8085-logical-rotate) |
| mp08 · Jumps, loops, stack and subroutines: largest number | [`mp08-8085-stack-subroutines`](mp08-8085-stack-subroutines) |
| mp10 · Interrupts, SIM and RIM: RST 7.5 counter | [`mp10-8085-interrupts`](mp10-8085-interrupts) |

## 8086 microprocessor (assembly: EMU8086 / MASM / TASM)

| Video | Folder |
|---|---|
| mp16 · Instruction set part 1: add five bytes (16-bit sum) | [`mp16-8086-data-transfer-arithmetic`](mp16-8086-data-transfer-arithmetic) |
| mp17 · Instruction set part 2: small letters to capitals | [`mp17-8086-logic-strings-jumps`](mp17-8086-logic-strings-jumps) |
| mp18 · A complete program with directives: largest number | [`mp18-8086-assembly-program`](mp18-8086-assembly-program) |
| mp19 · Interrupts: your own ISR as type 60H | [`mp19-8086-interrupts`](mp19-8086-interrupts) |

## Research tools (Python)

| Video | Folder |
|---|---|
| rv01 · Review paper workflow: search, duplicates, PDFs, citations | [`rv01-review-paper-tools`](rv01-review-paper-tools) |

## About the programs

* The 8085 programs (mp05 – mp10) and the 8086 programs of mp16 – mp18 were run in a simulator before
  publishing; the results match the videos.
* Addresses (2000H, 0100H, …) are the ones used in the videos; on a trainer kit with a different
  RAM area, change the start address and every address inside the program.
* Questions or a mistake? Open an *Issue* on this page or write a comment under the video.

## Licence

Code: MIT licence (see `LICENSE`). Fonts in `rv01-review-paper-tools/assets/` are under the SIL Open Font
License (see the file there).
