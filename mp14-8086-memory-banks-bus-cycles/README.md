# mp14 · 8086 Memory Banks Explained

How the 8086 reads 16 bits from byte-wide memory: the even and odd banks on D0-D7 and D8-D15, selection with A0 and BHE, the four cases, aligned and unaligned words (one or two bus cycles), little endian, a byte at an odd address, the four T-states of a bus cycle, read and write timing diagrams in minimum mode, and wait states.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.
Signals with a bar on top (R̅D̅) are active low.

### Memory banks and bus cycles  (00:00)

Today: how the 8086 memory is organized. The 8086 reads 16 bits at a time, but memory is still made of bytes. We will see the even and odd banks, how BHE and A0 select them, why words should be at even addresses, and the read and write bus cycles.

### Two banks  (00:21)

Memory is a list of bytes, one per address. The 8086 splits it into two banks. All the even addresses, 0, 2, 4 and so on, are in the even bank. All the odd addresses are in the odd bank. Each bank holds 512 KB.

### How the banks are connected  (00:39)

The even bank is connected to the lower half of the data bus, D0 to D7. The odd bank is connected to the upper half, D8 to D15. Address lines A1 to A19 go to both banks, and pick the same row in each.

### Selecting a bank  (00:55)

So how is a bank selected? The even bank is enabled when A0 is 0. The odd bank is enabled when BHE is 0. Both signals are active low here, so they can drive the chip selects directly.

### Four cases  (01:11)

This gives four cases. BHE 0 and A0 0: both banks, a whole word. BHE 0 and A0 1: only the odd bank, an odd byte, on D8 to D15. BHE 1 and A0 0: only the even bank, an even byte, on D0 to D7. And BHE 1 with A0 1: no bank.

| B̅H̅E̅ | A0 | enabled | transfer | lines |
|---|---|---|---|---|
| 0 | 0 | both banks | whole word | D0 – D15 |
| 0 | 1 | odd bank | odd byte | D8 – D15 |
| 1 | 0 | even bank | even byte | D0 – D7 |
| 1 | 1 | — | nothing | — |

### A word at an even address  (01:35)

Now a word at an even address. MOV AX, [2000H]. In one bus cycle, both banks are enabled. The byte at 2000H comes from the even bank into AL, and the byte at 2001H comes from the odd bank into AH. The low byte is at the lower address. This is called little endian.

### A word at an odd address  (02:00)

And a word at an odd address? MOV AX, [2001H]. The two bytes are now in different rows. So the 8086 needs two bus cycles. First it reads 2001H from the odd bank into AL. Then it reads 2002H from the even bank into AH. This takes twice as long. So keep word data at even addresses. This is called alignment.

### A byte at an odd address  (02:30)

A single byte at an odd address, like MOV AL, [2001H], needs only one bus cycle. BHE is 0 and A0 is 1, so the byte comes on D8 to D15, and the 8086 moves it internally into AL.

### One bus cycle  (02:47)

Now the bus cycle itself. Every memory or I/O access takes one bus cycle of four clock states, T1 to T4. In T1, the address goes out, and ALE latches it. In T2, the address is removed, the status comes out on the upper lines, and RD or WR goes low. In T3 the data is transferred, and T4 ends the cycle.

### Read cycle  (03:11)

Here is the read cycle in minimum mode. M/IO is high for memory for the whole cycle. ALE pulses in T1. The address is on AD0 to AD15 in T1, then the lines float, and the memory places its data from T3. RD is low from T2 to T4. DT/R is low, to receive, and DEN is low while the data is on the bus.

### Write cycle  (03:37)

The write cycle is similar. But now the 8086 itself drives the data, right from T2. WR goes low instead of RD. And DT/R is high, to transmit.

### Wait states  (03:51)

If the memory is slow, it pulls READY low. Then the 8086 adds wait states, Tw, between T3 and T4, until READY is high again. With a 5 MHz clock, one T-state is 200 nanoseconds, so a bus cycle without wait states takes 800 nanoseconds.

### Summary  (04:12)

Here is the summary. Memory is split into an even bank on D0 to D7 and an odd bank on D8 to D15. A0 selects the even bank, BHE selects the odd bank. An aligned word takes one bus cycle, an unaligned word takes two. And a bus cycle has four T-states, plus wait states if READY is low.

|   | remember |
|---|---|
| banks | even bank on D0–D7,  odd bank on D8–D15 |
| select | A0 = 0 → even,   B̅H̅E̅ = 0 → odd |
| words | aligned: 1 bus cycle,   unaligned: 2 |
| bus cycle | T1 – T4,  + Tw while READY = 0 |
