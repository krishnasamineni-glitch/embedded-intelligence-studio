# mp13 · 8086 Physical Address Calculation

Everything about the 8086 physical address: why two 16-bit numbers make a 20-bit address, the rule segment x 10H + offset, examples worked column by column with carries, the start and end of a segment, paragraphs, many logical addresses for one physical address, default segment registers (BP uses SS!), effective address examples, segment override, wrap-around past FFFFFH, finding the offset, and practice problems with answers.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.
Signals with a bar on top (R̅D̅) are active low.

### Physical address calculation  (00:00)

Today: physical address calculation in the 8086, step by step. We will work through many examples: simple ones, ones with a carry, the range of a segment, the default segment registers, segment override, and at the end some practice problems for you.

### Why two numbers?  (00:18)

The 8086 has 1 MB of memory, so every location needs a 20-bit address. But all its registers are only 16 bits. So an address is given as two 16-bit numbers: a segment and an offset. We write it as segment colon offset, for example 2000:0050. This is the logical address.

### The rule  (00:42)

The rule is: physical address equals segment times 10H, plus offset. Multiplying by 10H is easy in hex: just write a 0 at the end. In binary, it is a shift left by four bits. So 2000H becomes 20000H, which is now 20 bits long.

### Example 1  (01:02)

Example one. CS is 2500H and IP is 0123H. Shift CS: 25000H. Add IP: 25000H plus 0123H. The physical address is 25123H. This is where the next instruction is fetched from.

### Example 2: carries  (01:25)

Example two, with carries. DS is 1A2BH, and the offset is 9C55H. Shift DS: 1A2B0H. Now add column by column, from the right. 0 plus 5 is 5. B plus 5 is 16, which is 10H: write 0, carry 1. 2 plus C plus 1 is 15, which is F. A plus 9 is 19, which is 13H: write 3, carry 1. And 1 plus 1 is 2. The physical address is 23F05H.

### The range of a segment  (02:03)

A segment always starts at the segment value times 10H, with offset 0000H. And the offset can go up to FFFFH. So with DS equal to 3000H, the data segment starts at 30000H and ends at 30000H plus FFFFH, which is 3FFFFH. That is 64 KB.

### Segments start at multiples of 16  (02:30)

Notice that a segment always starts at an address whose last hex digit is 0. So a segment can start only at a multiple of 16 bytes. A block of 16 bytes is called a paragraph.

### One physical address, many logical addresses  (02:42)

Here is something interesting. Different logical addresses can point to the same physical address. 1000:2345, 1234:0005 and 1200:0345 all give 12345H. This happens because segments can overlap: a new segment can start every 16 bytes.

### Which segment register?  (03:08)

Which segment register is used? The 8086 decides by itself. Instructions are always fetched from CS, with IP. The stack uses SS, with SP, and also with BP. Data uses DS, with BX, SI, DI, or a direct address. And the string instructions write their destination in ES, with DI.

| used for | offset from | segment |
|---|---|---|
| instruction fetch | IP | CS |
| stack | SP,  BP | SS |
| data | BX,  SI,  DI,  direct address | DS |
| string destination | DI | ES |

### Example 3: BP + displacement  (03:32)

Example three, with BP. SS is 4000H and BP is 0200H. The instruction is MOV AX, [BP+10H]. First the offset, also called the effective address: 0200H plus 10H is 0210H. Because BP is used, the segment is SS. So the physical address is 40000H plus 0210H, which is 40210H.

### Example 4: BX + SI + displacement  (04:05)

Example four, with three parts. DS is 2000H, BX is 0100H, and SI is 0020H. The instruction is MOV AL, [BX+SI+05H]. The effective address is 0100H plus 0020H plus 05H, which is 0125H. The segment is DS, so the physical address is 20125H.

### Segment override prefix  (04:36)

We can also choose the segment ourselves, with a segment override prefix. MOV AL, ES:[BX] uses ES instead of DS. With ES equal to 5000H and BX equal to 0100H, the physical address is 50100H. Without the override, it would have used DS.

### Wrap-around  (04:58)

What if the sum is too big? FFFF:0010 gives FFFF0H plus 0010H, which is 100000H. That needs 21 bits, but the 8086 has only 20 address lines. So the top carry is lost, and the address wraps around to 00000H.

### The other way round  (05:23)

Sometimes the question is the other way round. The physical address is 2A3B5H, and DS is 2A00H. What is the offset? Subtract the segment base: 2A3B5H minus 2A000H is 03B5H. So the logical address is 2A00:03B5.

### Practice problems  (05:47)

Now try these yourself. Pause the video, and calculate. One: CS is 3456H, IP is 1234H. Two: SS is 0F00H, SP is FFFEH. Three: DS is ABCDH, and the offset is 1234H. The answers are: 35794H, 1EFFEH, and ACF04H.

### Summary  (06:15)

Here is the summary. Physical address equals segment times 10H, plus offset. Write a 0 after the segment, then add the offset in hex, carefully with carries. A segment covers 64 KB, starting at a multiple of 16. The register used for the offset decides the default segment, and a prefix can override it.

|   | remember |
|---|---|
| rule | physical = segment × 10H + offset |
| how | write a 0 after the segment, add in hex with carries |
| segment | 64 KB, starts at a multiple of 16 |
| which segment | chosen by the offset register; a prefix overrides |
