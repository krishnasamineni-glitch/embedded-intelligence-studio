# mp18 · Writing a Complete 8086 Program: Directives and the Largest Number

Programs from the video **8086 Assembly Program with Directives** (SEGMENT/ENDS, ASSUME, DB/DW/DD, DUP,
EQU, OFFSET, PTR, PROC/ENDP, END, loading DS, INT 21H).

| File | What it does |
|---|---|
| `largest.asm` | The complete program from the video: finds the largest of five bytes and stores it in `LARGEST` |
| `skeleton.asm` | The skeleton every program starts from |

## Result

`NUMS` = 23H, 8AH, 45H, 9CH, 61H → `LARGEST` = **9CH**.
In memory: `NUMS` at offset 0000H of the data segment, `LARGEST` at 0005H.
AL goes 23H → 8AH → (keeps 8AH for 45H) → 9CH → (keeps 9CH for 61H).

## Common mistakes

* Forgetting `MOV DS, AX`: the program reads the wrong memory.
* Writing `MOV DS, DATA`: a segment register cannot be loaded with a value directly.
* Forgetting `END START`.
* Using `JG` instead of `JA` for unsigned bytes: 8AH and 9CH would look negative.

## How to run it

In EMU8086: *New* → *empty workspace*, paste `largest.asm`, press **emulate**, step through the loop
and watch AL; at the end look at `LARGEST` in the variables window.
With MASM: `masm largest.asm;` → `link largest.obj;` → step through `largest.exe` in DEBUG / CodeView.
With TASM: `tasm largest.asm` → `tlink largest.obj`.
