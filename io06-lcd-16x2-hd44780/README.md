# io06 · 16x2 LCD Interfacing Explained

The 16x2 character LCD with the HD44780 controller: the pins, RS / RW / E and the two registers, one write cycle and the falling edge of E, 4-bit mode with two nibbles, the commands 0x28, 0x0C, 0x06, 0x01 and 0x80 + address, DDRAM addresses (line 2 starts at 0x40), ASCII characters, the start-up sequence 3, 3, 3, 2, wiring on one port and using a 5 V module with 3.3 V, the driver code, an emulator run with a model of the HD44780 that decoded the pins, custom characters in CGRAM, the busy flag, and a practice question.

## Files

* [`lcd_demo.c`](lcd_demo.c) – a 16x2 character LCD (HD44780) in 4-bit mode (LPC1768)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_lcd.py`](test_lcd.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_lcd.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### The 16x2 character LCD  (00:00)

Today: the 16 by 2 character LCD, the classic display of embedded projects. We will see its pins, its two registers, how one write works with the E pulse, the 4-bit mode, the commands and the start-up sequence, and how to place text and even draw our own characters. The code runs on an LPC1768, and on an emulated Cortex-M3 a model of the LCD controller showed exactly the text it should.

### The module  (00:31)

The module shows 2 lines of 16 characters. On its back sits a controller, the HD44780 or a compatible chip, which stores the text and draws the characters by itself. It has 16 pins: power and ground, a contrast pin with a potentiometer, three control pins named RS, RW and E, eight data pins D0 to D7, and two pins for the backlight. Once a character is written, the controller keeps showing it, so the processor does not have to refresh anything.

### RS, RW and E  (01:03)

The three control pins decide what a write means. RS selects the register: 0 for the instruction register, which takes commands, and 1 for the data register, which takes characters. RW selects read or write, and since we only write, RW is tied to ground. E is the enable pin: the LCD takes the value on the data pins when E goes from high to low.

### One write  (01:28)

So one write goes like this. Set RS, put the byte on the data pins, raise E, wait at least 450 nanoseconds, and pull E low. On that falling edge, the LCD takes the byte. Then it needs time to do the work: about 37 microseconds for most commands, and 1.52 milliseconds to clear the display.

### 4-bit mode  (01:51)

Eight data pins plus RS and E would need 10 pins. In 4-bit mode, only D4 to D7 are used, and each byte is sent in two halves: first the high nibble, then the low nibble, each with its own E pulse. That brings it down to 6 pins, at the cost of a slightly longer write. This is how most projects connect the LCD.

### The commands  (02:14)

Here are the commands we need. 0x28 sets 4-bit mode with 2 lines. 0x0C switches the display on with the cursor off, 0x06 moves the cursor to the right after each character, and 0x01 clears the screen. And a command with the top bit set, 0x80 plus an address, moves the cursor.

| command | what it does |
|---|---|
| 0x28 | function set: 4-bit, 2 lines, 5 × 8 dots |
| 0x0C | display on, cursor off |
| 0x06 | entry mode: move right after each character |
| 0x01 | clear the display (1.52 ms) |
| 0x80 + address | set the cursor (DDRAM address) |

### DDRAM addresses  (02:37)

The text lives in the display RAM, called DDRAM. On a 16 by 2 display, line 1 uses the addresses 0x00 to 0x0F, and line 2 starts at 0x40, not at 0x10. So to go to line 2, column 0, we send 0x80 plus 0x40, which is 0xC0. In general, the command is 0x80, plus 0x40 for line 2, plus the column.

### Characters: ASCII codes  (03:05)

Characters are sent with RS equal to 1, as plain ASCII codes. H is 0x48, e is 0x65, and the LCD has the pictures of these characters in its own font ROM. After each character, the cursor moves one place to the right by itself.

### The start-up sequence  (03:24)

At power on, the LCD may not know whether it is in 8-bit or 4-bit mode, so there is a fixed start-up sequence. Wait more than 40 milliseconds, then send the nibble 3 three times, with short waits, which puts it in 8-bit mode for sure. Then the nibble 2 switches it to 4-bit mode. From here on, every byte goes as two nibbles: 0x28, 0x0C, 0x06 and 0x01.

### Wiring  (03:53)

Our wiring uses one port. RS is on P2.0, E on P2.1, and D4 to D7 on P2.4 to P2.7, and RW goes to ground. Many of these modules run on 5 volts, but with RW at ground the LCD never drives the data lines, and it reads 3.3 volts as a valid high level.

### The low-level code  (04:16)

Here is the low-level code. lcd_nibble puts four bits on D4 to D7 with FIOCLR2 and FIOSET2, then sets E, waits a microsecond, and clears E. lcd_byte sets or clears RS, and sends the high nibble first, then the low nibble. Then it waits 50 microseconds, which is enough for most commands, and lcd_cmd adds 2 milliseconds after a clear.

### lcd_init, lcd_goto, lcd_print  (04:45)

lcd_init does the start-up sequence in code. It makes the six pins outputs, waits 50 milliseconds, sends 3, 3, 3 and 2 as single nibbles, and then the four commands. lcd_goto builds the 0x80 command from the line and the column, and lcd_print sends one character after another.

### On the emulator  (05:06)

On the emulator, a model of the HD44780 watched the pins, and took a nibble on every falling edge of E. It saw 3, 3, 3 and 2, then the bytes 0x28, 0x0C, 0x06 and 0x01, then 0x80 and the characters. At the end, its display RAM held both lines of text, exactly as written. And with the real delay, E stayed high for more than one and a half microseconds, well above the 450 nanoseconds.

### Custom characters: CGRAM  (05:39)

The controller also has room for 8 characters of our own, in CGRAM. Each one is 8 rows of 5 dots, so 8 bytes, where the low 5 bits of each byte are the dots of one row. The command 0x40 plus 8 times n selects character n, and then we write its 8 rows as data. After that, writing the character code n shows our own symbol, like this heart at the end of line 2.

### The busy flag  (06:05)

Instead of fixed waits, a program can also read the busy flag. With RW at 1, D7 reads 1 while the LCD is still working, so the program waits exactly as long as needed. That needs the RW pin, and data pins that can switch to inputs, so fixed delays are the simpler choice.

### Practice  (06:25)

Now try this yourself. Pause the video. Which command puts the cursor on line 2, column 5? And which byte do we send to show the letter A? The answers: 0x80 plus 0x40 plus 5, which is 0xC5, and the ASCII code of A, 0x41, sent with RS equal to 1.

### Summary  (06:46)

Here is the summary. The HD44780 has two registers, RS 0 for commands and RS 1 for characters, and it takes a value on the falling edge of E. In 4-bit mode, each byte goes as two nibbles, high first, over D4 to D7, so 6 pins are enough. Start with the fixed sequence 3, 3, 3, 2, then 0x28, 0x0C, 0x06 and 0x01, and remember that line 2 starts at the address 0x40.

|   | remember |
|---|---|
| RS | 0 = command, 1 = character |
| E | the LCD takes the value on the falling edge |
| 4-bit mode | two nibbles, high first, on D4 .. D7: 6 pins |
| start-up | 3, 3, 3, 2, then 0x28, 0x0C, 0x06, 0x01 |
| DDRAM | line 1 at 0x00, line 2 at 0x40: cursor = 0x80 + address |
