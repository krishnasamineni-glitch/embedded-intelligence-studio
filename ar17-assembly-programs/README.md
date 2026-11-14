# ar17 · 6 ARM Assembly Programs

Six complete ARM Cortex-M3 assembly programs, explained step by step with 32-bit values: the sum of an array with post-indexed loads, the largest signed number with an IT block, counting the 1 bits of a word with LSRS and ADC, 10 factorial with MUL, the greatest common divisor with ITE and no branch inside the loop, and bubble sort with conditional stores. Plus the patterns they share and how to try them in Keil. Every program was run in an ARM emulator.

## Files

* [`programs_demo.s`](programs_demo.s) – the six complete programs of the video and the practice loop, ready to step through in Keil

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Six complete assembly programs  (00:00)

Today we put the instructions together into six complete ARM Cortex-M3 assembly programs. The sum of an array, the largest number, counting bits, factorial, the greatest common divisor, and bubble sort. Every program was run in an ARM emulator, so all the results are real.

### Program 1: sum of an array  (00:20)

Program one adds the five words of an array: 10, 20, 30, 40 and 50. R0 points to the array, R2 holds the sum, and R3 counts the elements. LDR R1, [R0], #4 loads the next element and moves the pointer on by 4 in the same instruction. SUBS and BNE repeat this five times, and R2 ends at 150.

### Program 2: the largest signed number  (00:46)

Program two finds the largest signed number in 5, minus 3, 42, 17 and minus 8. R2 starts with the first element, and the loop compares every other element with it. CMP R1, R2 followed by an IT GT block keeps the new value only when it is greater. After four passes, R2 is 42.

### Program 3: count the 1 bits  (01:08)

Program three counts the 1 bits of 0xF0F0F0F0. LSRS shifts the word right by one, and the bit that falls out goes into the carry flag. ADC R1, R1, #0 then adds the carry to the count. Because ADC has no S, it keeps the Z flag of LSRS, so BNE stops as soon as no 1 bits are left. The count is 16.

### Program 4: factorial  (01:37)

Program four computes 10 factorial. R0 starts at 1, and MUL multiplies it by R1, which counts down from 10 to 1. The result is 3628800, which is 0x00375F00. Note that 12 factorial is the largest that fits into 32 bits: 13 factorial would overflow.

| R1 | R0 |
|---|---|

### Program 5: greatest common divisor  (02:02)

Program five finds the greatest common divisor of 48 and 18, with Euclid's method. Subtract the smaller number from the larger one, until both are equal. Here an ITE GT block does it without any branch inside the loop: SUBGT works when R0 is larger, and SUBLE when it is not. The pairs go 48 and 18, 30 and 18, 12 and 18, 12 and 6, and then 6 and 6. So the answer is 6.

| R0 | R1 | next step |
|---|---|---|
| 48 | 18 | R0 − R1 |
| 30 | 18 | R0 − R1 |
| 12 | 18 | R1 − R0 |
| 12 | 6 | R0 − R1 |
| 6 | 6 | equal: stop |

### Program 6: bubble sort  (02:34)

Program six sorts five signed numbers: 42, 7, minus 3, 19 and 0. Bubble sort compares neighbours, and swaps them when they are in the wrong order. Two loops do it: an outer loop for the passes, and an inner loop for the pairs. The swap is just two stores, made conditional with an ITT GT block.

### Bubble sort pass by pass  (02:57)

After the first pass, the largest number, 42, has moved to the end. Every pass needs one comparison less. After four passes, the array is minus 3, 0, 7, 19 and 42.

### Patterns you will use again  (03:10)

These programs share a few patterns. A pointer register walks through memory with post-indexed loads. A counter counts down to zero, so SUBS and BNE close the loop. And small decisions use IT blocks instead of branches.

### Trying a program in Keil  (03:26)

To try a program in Keil, put it into a function and call it from C. The arguments arrive in R0 to R3, and the result goes back in R0. Then step through it in the debugger, and watch the registers and a memory window at 0x2007C000.

### Practice  (03:44)

Now try this yourself. Pause the video. R0 starts at 0 and R1 at 1, and the loop adds R1 to R0, adds 1 to R1, and repeats until R1 is 101. What is R0 at the end? The answer: 5050, the sum of the numbers from 1 to 100.

### Summary  (04:06)

Here is the summary. We added an array, found the largest number, counted bits with the carry flag, computed a factorial, found a greatest common divisor, and sorted an array. Pointers with post-indexed loads, count-down loops and IT blocks appear again and again. Write these programs yourself, and step through them in the debugger.

| program | idea | result |
|---|---|---|
| 1  sum of an array | post-indexed LDR, count down | 150 |
| 2  largest number | CMP + IT GT | 42 |
| 3  count 1 bits | LSRS + ADC: the carry flag | 16 |
| 4  factorial | MUL in a loop | 3628800 |
| 5  GCD | ITE GT: no branch inside | 6 |
| 6  bubble sort | two loops, ITT GT swap | −3 0 7 19 42 |
