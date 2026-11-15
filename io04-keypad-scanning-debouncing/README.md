# io04 · 4x4 Keypad Interfacing Explained

How a microcontroller reads a 4x4 matrix keypad: why a matrix puts 16 keys on 8 pins, rows and columns with pull-ups, scanning one row at a time, a worked example (key 6), why only the scanned row should be an output, the setup and scan code with real register values, how often to scan, contact bounce, three ways to debounce, a sampling debouncer that reports each press once, ghost keys and how to avoid them, and a practice question. The code was run on an emulated Cortex-M3 with a model of the keypad.

## Files

* [`keypad_demo.c`](keypad_demo.c) – the 4x4 keypad of the video (LPC1768)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_keypad.py`](test_keypad.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_keypad.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Reading a 4x4 keypad  (00:00)

Today: reading a 4 by 4 keypad with a microcontroller. We will see how 16 keys share only 8 pins, how scanning finds the pressed key, why keys bounce and how to debounce them, and what ghost keys are. The code runs on an LPC1768, and it was checked on an emulated Cortex-M3 with a model of the keypad.

### Why a matrix?  (00:24)

If every key had its own pin, 16 keys would need 16 pins. A keypad puts the keys in a matrix of 4 rows and 4 columns instead. Each key sits where a row line crosses a column line, and pressing it connects that row to that column. So 16 keys need only 8 pins: 4 for the rows and 4 for the columns.

### Wiring: rows and columns  (00:45)

In our example, the rows are on P2.0 to P2.3, and the columns are on P2.4 to P2.7. The column pins are inputs with the internal pull-up resistors switched on. With no key pressed, every column reads 1.

### Scanning the rows  (01:01)

To find a key, we scan the rows one at a time. We pull one row low and read the four columns. If a key in that row is pressed, it connects its column to the low row, so that column reads 0. Then we release the row and go on to the next one.

### Example: key 6  (01:18)

Suppose key 6 is pressed. It sits in row 1, column 2. When row 0 is low, all four columns read 1, so no key in row 0 is pressed. When row 1 is low, column 2 reads 0. The key number is row times 4 plus column, so 1 times 4 plus 2 gives 6, and a small table turns this number into the character on the key.

| row low | C3 C2 C1 C0 | result |
|---|---|---|
| R0 | 1 1 1 1 | no key in row 0 |
| R1 | 1 0 1 1 | column 2 is 0 |

### Only the scanned row is an output  (01:43)

There is one detail in how we drive the rows. If all four rows were outputs, one low and three high, then pressing two keys in the same column would connect a high output directly to a low output, which is a short circuit. So only the row being scanned is an output, driven low. The other rows are inputs, held high by their pull-ups, so nothing can be shorted.

### Setup  (02:07)

The setup is short. PINSEL4 makes P2.0 to P2.7 GPIO pins, and PINMODE4 switches on their pull-ups. All eight pins start as inputs, and FIOCLR2 sets the output value of the four rows to 0, so a row goes low as soon as we make it an output.

| register | write |
|---|---|
| PINSEL4 | bits 15:0 = 0 |
| PINMODE4 | bits 15:0 = 0 |
| FIODIR2 | bits 7:0 = 0 |
| FIOCLR2 | 0x0000000F |

### The scan  (02:27)

Here is the scan. For each row, we make only that row an output by writing FIODIR2, wait a moment for the lines to settle, and read the columns from bits 7 to 4 of FIOPIN2. If a column bit is 0, we return row times 4 plus column. If no column is low in any row, we return minus 1, which means no key.

### On the emulator: key 6  (02:50)

On the emulator, with a model of the keypad, we pressed key 6. When row 0 was the output, bits 7 to 4 of FIOPIN2 read 1111, and when row 1 was the output, they read 1011, so column 2 was the 0. The scan returned 6, and the table gave the character 6.

| output | FIODIR2 3:0 | FIOPIN2 7:4 | low |
|---|---|---|---|
| R0 | 0001 | 1111 | none |
| R1 | 0010 | 1011 | C2 |

### How often to scan  (03:10)

A full scan of four rows takes only a few microseconds. A human key press lasts a hundred milliseconds or more, so scanning every 5 to 20 milliseconds never misses a key. This is usually done from a timer interrupt, like SysTick, so the main program does not have to wait.

### Switches bounce  (03:27)

Now a problem: switches bounce. When the metal contacts of a key close, they hit and spring apart several times before they settle. This lasts from about one to twenty milliseconds. So a fast program can read one press as many presses.

### Three ways to debounce  (03:43)

There are three common ways to debounce. The simplest is to wait about 20 milliseconds after a change and read again, but the processor wastes that time. A better way is to sample every few milliseconds and accept a new state only after it has been the same several times in a row. In hardware, a resistor, a capacitor and a Schmitt trigger input can smooth the bounce.

### Debouncing by sampling  (04:07)

Here is the sampling method. key_event is called every 5 milliseconds, and it scans the keypad. It counts how many times in a row the result has been the same. When the same result has been seen 4 times, that is 20 milliseconds, it becomes the new stable state, and a press is reported once.

### On the emulator: a bouncing key  (04:26)

We fed it a bouncing press of key 5 on the emulator. The first samples flicker between pressed and not pressed, and the counter keeps starting again. Only after four pressed samples in a row does key_event return 5, and just once. The bouncing release reports nothing, and the next press is reported again.

### Ghost keys  (04:46)

One more effect: ghost keys. Press keys 1, 3 and 7 together. When row 2 is pulled low, the low level spreads through key 7 to column 0, through key 1 to row 0, and through key 3 to column 2. So column 2 also reads 0, and the scanner sees key 9, which nobody pressed. Computer keyboards prevent this with a diode in series with every key, and with a simple keypad, the program can ignore a reading with more than one column low.

### Practice  (05:16)

Now try this yourself. Pause the video. Row 2 is low, and bits 7 to 4 of FIOPIN2 read 1101. Which key is pressed? Column 1 is the 0, so the key number is 2 times 4 plus 1, which is 9, and the table gives the character 8.

### Summary  (05:35)

Here is the summary. A 4 by 4 keypad needs 8 pins: the rows are driven low one at a time, and the columns are read with pull-ups. The low column in the scanned row gives the key, row times 4 plus column. Sampling every 5 milliseconds and waiting for 4 equal samples removes the bounce. And when three keys are pressed together, watch out for ghost keys.

|   | remember |
|---|---|
| matrix | 16 keys on 8 pins: 4 rows + 4 columns |
| scan | one row low (only it an output), read the columns |
| key number | row × 4 + column → keymap |
| debounce | every 5 ms, 4 equal samples = 20 ms |
| ghost keys | 3 keys pressed: diodes, or ignore 2+ low columns |
