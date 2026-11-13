# mp17 · 8086 Instruction Set, Part 2: Logic, Shifts, Strings and Jumps

Program from the video **8086 Instruction Set Part 2** (AND/OR/XOR/NOT/TEST, SHL/SHR/SAR, rotates,
string instructions with REP, jumps, JA vs JG, LOOP, CALL).

| File | What it does |
|---|---|
| `upper.asm` | Copies a text and changes small letters to capitals, with `LODSB` / `STOSB` (assembler version) |

## Trainer kit version (as in the video)

| Address | Code | Instruction | Comment |
|---|---|---|---|
| 0100H | `BE 00 05` | `MOV SI, 0500H` | source |
| 0103H | `BF 00 06` | `MOV DI, 0600H` | destination |
| 0106H | `B9 05 00` | `MOV CX, 0005H` | 5 characters |
| 0109H | `FC` | `CLD` | forward |
| 010AH | `AC` | `NEXT: LODSB` | AL = char |
| 010BH | `3C 61` | `CMP AL, 'a'` |  |
| 010DH | `72 06` | `JB STORE` | below a |
| 010FH | `3C 7A` | `CMP AL, 'z'` |  |
| 0111H | `77 02` | `JA STORE` | above z |
| 0113H | `2C 20` | `SUB AL, 20H` | to capital |
| 0115H | `AA` | `STORE: STOSB` | store |
| 0116H | `E2 F2` | `LOOP NEXT` | repeat |
| 0118H | `F4` | `HLT` | stop |

On the kit, DS = ES, so `STOSB` (which writes to ES:DI) stores into the same segment.

## Test data

| Address | Before | After |
|---|---|---|
| 0500H – 0504H | `48 69 20 38 36` = "Hi 86" | unchanged |
| 0600H – 0604H | – | `48 49 20 38 36` = **"HI 86"** |

'H' is already a capital; 'i' (69H) − 20H = 49H ('I'); the space and the digits are below 'a', so they are copied unchanged.
`JB` / `JA` are the unsigned jumps, which is right for character codes.

## How to run it

**Assembler version (`.asm`)**: works with EMU8086, MASM and TASM.
In EMU8086: *New* → *empty workspace*, paste the file, press **emulate**, then **run** (or step with
**single step** and watch the registers and memory).
With MASM: `masm file.asm;` → `link file.obj;` → run `file.exe` (or step through it in DEBUG / CodeView).
With TASM: `tasm file.asm` → `tlink file.obj` → run.

**Trainer kit version (the table above)**: enter the code bytes from 0100H, store the input bytes,
run from 0100H, and examine the result. The kit version uses fixed addresses and ends with `HLT`;
the `.asm` version uses names for the data and returns to DOS with `MOV AH, 4CH` / `INT 21H`
(see video mp18).
