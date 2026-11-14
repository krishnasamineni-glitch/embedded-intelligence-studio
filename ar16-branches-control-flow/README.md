# ar16 · ARM Branches and Control Flow

How the ARM Cortex-M3 decides, loops and calls functions: B and the program counter, condition codes, unsigned (HI, HS, LO, LS) and signed (GT, GE, LT, LE) comparisons with 0xFFFFFFFF as an example, if and else with branches and with IT blocks, count-down loops, CBZ and CBNZ, BL, BX LR and nested calls with PUSH and POP, BX and BLX with a register, TBB switch tables, the cost of a taken branch, and SVC, CPSID, CPSIE, WFI and the barriers DMB, DSB and ISB. Every example was run in an ARM emulator.

## Files

* [`branch_demo.s`](branch_demo.s) – every branch example of the video: conditions, if / else, IT, loops, CBZ, BL, TBB
* [`verify_run.py`](verify_run.py) – runs any of these .s files in an emulator and checks the comments (pip install keystone-engine unicorn;  python verify_run.py branch_demo.s)

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Branches and control flow  (00:00)

Today: branches and control flow on the ARM Cortex-M3. We will see conditional branches, loops, if and else, function calls, switch statements, and a few special control instructions, all checked in an ARM emulator.

### A branch writes the PC  (00:16)

A program normally runs from one instruction to the next, as the program counter moves forward. A branch simply writes a new address into the PC. The B instruction always jumps to its label, and its 32-bit form reaches about 16 megabytes forward or backward.

### Conditional branches  (00:33)

Add a condition code, and the branch is taken only when the flags match. BEQ branches if equal, which means Z is 1, and BNE branches if not equal. The simple conditions test one flag each: EQ and NE test Z, CS and CC test C, MI and PL test N, and VS and VC test V.

| code | meaning | test |
|---|---|---|
| EQ | equal | Z = 1 |
| NE | not equal | Z = 0 |
| CS / HS | carry set | C = 1 |
| CC / LO | carry clear | C = 0 |
| MI | minus, negative | N = 1 |
| PL | plus, positive or zero | N = 0 |
| VS | overflow | V = 1 |
| VC | no overflow | V = 0 |

### Unsigned and signed conditions  (00:55)

For comparisons, unsigned numbers use HI, HS, LO and LS: higher, higher or same, lower, and lower or same. Signed numbers use GT, GE, LT and LE: greater than, greater or equal, less than, and less or equal.

### Same bits, different answers  (01:14)

This matters. Compare R0 equal to 0xFFFFFFFF with R1 equal to 1. As an unsigned number, R0 is the largest 32-bit value, so BHI is taken. But as a signed number, R0 is minus 1, so BGT is not taken. The same bits and the same flags: only the condition decides.

### if / else with branches  (01:37)

An if and else becomes a compare and two branches. To put the larger signed number in R2, we compare R0 with R1, branch to the else part if R0 is less, otherwise copy R0, and then jump over the else part. With R0 equal to minus 5 and R1 equal to 3, R2 becomes 3.

### if / else with an IT block  (01:58)

Short if and else parts are better with an IT block. ITE GE means: if greater or equal, then run the next instruction, else run the one after it. So MOVGE R2, R0 and MOVLT R2, R1 do the same job, without any branch. An IT block can hold up to four conditional instructions.

### Loops  (02:20)

Loops are branches backwards. This loop adds 10, 9, 8, and so on, down to 1. SUBS decreases the counter and sets the Z flag when it reaches zero, so BNE repeats the loop until then. At the end, R0 is 55. Counting down to zero saves a compare instruction in every pass.

### CBZ and CBNZ  (02:42)

CBZ and CBNZ compare a register with zero and branch, in a single instruction, without changing the flags. Here CBZ stops a loop at the zero byte that ends a string. For the string ARM, R1 ends at 3. They can only branch a short distance forward, and only with registers R0 to R7.

### Functions: BL and BX LR  (03:04)

Functions are called with BL, branch with link. BL writes the return address into the link register, LR, and then jumps. The function returns with BX LR, which copies LR back into the PC. So with R0 equal to 7, BL square returns with R0 equal to 49.

### Nested calls: PUSH and POP  (03:23)

But if a function calls another function, the second BL overwrites LR. So such a function first saves LR on the stack with PUSH, together with the registers it uses, like R4. At the end, POP {R4, PC} restores R4 and loads the return address straight into the PC, which returns. Our sum of squares function calls square twice, and 3 squared plus 4 squared gives 25.

### BX and BLX with a register  (03:49)

BX and BLX can also branch to an address held in any register, which is how function pointers work. On the Cortex-M3, bit 0 of that address must be 1, because the processor only runs Thumb code. If bit 0 is 0, the processor raises a usage fault.

### Switch tables: TBB and TBH  (04:07)

A switch statement can use a table branch. TBB, table branch byte, reads a byte from a table at PC plus R0, doubles it, and adds it to the PC. With R0 equal to 2, it jumps to case 2, and R1 becomes 30. TBH does the same with a table of halfwords, for longer jumps.

### The cost of a branch  (04:28)

Branches have a cost. When a branch is taken, the instructions already fetched by the three-stage pipeline are thrown away, so a taken branch takes about two to four cycles. A branch that is not taken costs just one cycle. This is why IT blocks and counting down to zero make small loops and decisions faster.

### SVC, CPSID, WFI and barriers  (04:49)

A few control instructions are special. SVC, supervisor call, raises an exception on purpose, and is how programs ask an operating system for a service. CPSID I and CPSIE I disable and enable interrupts, by setting and clearing PRIMASK. WFI, wait for interrupt, puts the processor to sleep until an interrupt arrives. And the barriers DMB, DSB and ISB make sure that memory accesses and instruction fetches happen in order, for example after changing the vector table.

### Practice  (05:24)

Now try this yourself. Pause the video. R0 starts at 1 and R1 at 5, and the loop shifts R0 left by 1, decreases R1, and repeats while R1 is not zero. What is R0 at the end? The answer: 32, because R0 is doubled five times.

| pass | R0 | R1 |
|---|---|---|
| 1 | 2 | 4 |
| 2 | 4 | 3 |
| 3 | 8 | 2 |
| 4 | 16 | 1 |
| 5 | 32 | 0 |

### Summary  (05:44)

Here is the summary. B jumps, and a condition code makes it conditional, with HI, HS, LO and LS for unsigned numbers, and GT, GE, LT and LE for signed numbers. IT blocks replace short branches, and counting down to zero gives the fastest loops. CBZ and CBNZ test for zero, BL calls and BX LR returns, and PUSH and POP save LR in nested calls. TBB and TBH build switch statements.

|   | remember |
|---|---|
| B, Bcc | jump; jump if the condition is true |
| HI HS LO LS | unsigned comparisons |
| GT GE LT LE | signed comparisons |
| IT | conditional instructions, no branch |
| SUBS + BNE | count down to zero: fast loops |
| CBZ  CBNZ | branch if a register is zero / not zero |
| BL,  BX LR | call and return;  PUSH / POP save LR |
| TBB  TBH | switch tables |
