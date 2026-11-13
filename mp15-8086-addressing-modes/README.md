# mp15 · 8086 Addressing Modes

Every addressing mode of the 8086 with the same register values, so you can compare them: immediate, register, direct, register indirect, based (with BX and with BP), indexed, based indexed and based indexed with displacement, each with the effective address and the physical address worked out; then the one formula, string, I/O, relative and implied addressing, and a summary table.

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.
Signals with a bar on top (R̅D̅) are active low.

### Addressing modes  (00:00)

Today: the addressing modes of the 8086. An addressing mode tells the processor where to find the data. For every mode that uses memory, we will calculate the effective address and the physical address, step by step.

### The values  (00:16)

For all the examples we use the same values. DS is 2000H and SS is 3000H. BX is 0100H, BP is 0200H, SI is 0010H, and DI is 0020H. Keep these in mind; they stay on the screen.

### Immediate  (00:40)

First, immediate addressing. MOV AX, 1234H. The data, 1234H, is part of the instruction itself. No memory address is needed for the data. After the instruction, AX holds 1234H.

### Register  (00:57)

Register addressing. MOV AX, BX. Both operands are registers, so the data never leaves the processor. This is the fastest mode. AX becomes 0100H.

### Direct  (01:11)

Direct addressing. MOV AX, [5000H]. The offset is written in the instruction: the effective address is 5000H. The segment is DS. So the physical address is 20000H plus 5000H, which is 25000H.

### Register indirect  (01:34)

Register indirect addressing. MOV AX, [BX]. The offset is in a register: BX, SI or DI. The effective address is the value of BX, 0100H. With DS, the physical address is 20100H. Change BX, and the same instruction reads a different location. That is how we walk through an array.

### Based  (02:00)

Based addressing. MOV AX, [BX+08H]. A base register plus a displacement. The effective address is 0100H plus 08H, which is 0108H, and the physical address is 20108H. If the base register is BP, the segment is SS. So MOV AX, [BP+08H] gives 0208H, and the physical address is 30208H.

### Indexed  (02:33)

Indexed addressing. MOV AX, [SI+05H]. An index register, SI or DI, plus a displacement. The effective address is 0010H plus 05H, which is 0015H. The physical address is 20015H. Here the displacement can be the start of a table, and SI the position inside it.

### Based indexed  (02:59)

Based indexed addressing. MOV AX, [BX+SI]. A base register plus an index register. The effective address is 0100H plus 0010H, which is 0110H. The physical address is 20110H. Think of BX as the start of a table, and SI as the position inside it.

### Based indexed with displacement  (03:24)

Based indexed with displacement. MOV AX, [BX+DI+04H]. All three parts. The effective address is 0100H plus 0020H plus 04H, which is 0124H, so the physical address is 20124H. With BP instead: MOV AX, [BP+SI+04H] gives 0214H, in the stack segment, so 30214H.

### One formula  (03:55)

So all the memory modes follow one formula. Effective address equals base plus index plus displacement. The base is BX or BP, or nothing. The index is SI or DI, or nothing. And the displacement is 8 or 16 bits, or nothing. If BP is used, the segment is SS; otherwise it is DS.

### String addressing  (04:19)

String addressing. A string instruction like MOVSB uses two addresses at once. The source is DS:SI, and the destination is ES:DI. After every byte, SI and DI move to the next byte, up or down, depending on the direction flag.

### I/O addressing  (04:37)

I/O addressing. IN AL, 80H reads from port 80H: the port number is in the instruction, so only ports 00H to FFH can be used. IN AL, DX takes the port number from DX. Then all 65,536 ports are possible.

### Relative addressing  (04:58)

Relative addressing is used by the jumps. JNZ with a displacement adds a signed 8-bit number to IP. For example, a JNZ at offset 0100H is two bytes long, so IP points to 0102H. With a displacement of F0H, which is minus 16, the jump goes to 00F2H.

### Implied addressing  (05:21)

And implied addressing: the instruction itself says what it works on. CLC clears the carry flag, and STD sets the direction flag. No operand is written at all.

### Summary  (05:33)

Here is the summary of the modes that use memory, with our values. Direct: 25000H. Register indirect: 20100H. Based with BX: 20108H, and with BP: 30208H. Indexed: 20015H. Based indexed: 20110H. And with displacement: 20124H.

| mode | operand | EA | physical |
|---|---|---|---|
| direct | [5000H] | 5000H | 25000H |
| register indirect | [BX] | 0100H | 20100H |
| based (BX) | [BX+08H] | 0108H | 20108H |
| based (BP) | [BP+08H] | 0208H | 30208H |
| indexed | [SI+05H] | 0015H | 20015H |
| based indexed | [BX+SI] | 0110H | 20110H |
| based indexed + disp | [BX+DI+04H] | 0124H | 20124H |
