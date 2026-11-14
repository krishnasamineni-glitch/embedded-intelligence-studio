; memory_demo.s - the examples of the "memory access" video, ARM Cortex-M3 (Keil uVision, ARM assembler).
; It uses the LPC1768 AHB SRAM at 0x2007C000 as a scratch area (free in a normal Keil project).
; Call it from C:   extern void memory_demo(void);   memory_demo();
; Step through it in the debugger: compare each register with the comment, and watch 0x2007C000 in a Memory window.

        AREA    MemoryDemo, CODE, READONLY
        THUMB
        EXPORT  memory_demo

memory_demo
        PUSH    {R4-R6, LR}

        ; ---- fill an array of words: 0x11111111, 0x22222222, 0x33333333, 0x44444444 -----------
        LDR     R1, =0x2007C000
        LDR     R0, =0x11111111
        STR     R0, [R1]
        LDR     R0, =0x22222222
        STR     R0, [R1, #4]
        LDR     R0, =0x33333333
        STR     R0, [R1, #8]
        LDR     R0, =0x44444444
        STR     R0, [R1, #12]
        LDR     R0, =0x1234F680
        STR     R0, [R1, #16]           ; the word used for the byte and halfword loads

        ; ---- bytes and halfwords (little endian: the lowest address holds 0x80) -----------------
        ADD     R2, R1, #16             ; R2 = 0x2007C010
        LDRB    R0, [R2]                ; R0 = 0x00000080   (128)
        LDRSB   R0, [R2]                ; R0 = 0xFFFFFF80   (-128)
        LDRH    R0, [R2]                ; R0 = 0x0000F680
        LDRSH   R0, [R2]                ; R0 = 0xFFFFF680

        ; ---- offset, pre-indexed, post-indexed ---------------------------------------------------
        LDR     R0, [R1, #4]            ; R0 = 0x22222222   R1 = 0x2007C000   (R1 unchanged)
        MOV     R3, R1
        LDR     R0, [R3, #4]!           ; R0 = 0x22222222   R3 = 0x2007C004   (pre-indexed, write-back)
        MOV     R3, R1
        LDR     R0, [R3], #4            ; R0 = 0x11111111   R3 = 0x2007C004   (post-indexed)
        LDR     R0, [R3], #4            ; R0 = 0x22222222   R3 = 0x2007C008   (next element)

        ; ---- register offset: element R2 of a word array ------------------------------------------
        MOVS    R2, #3
        LDR     R0, [R1, R2, LSL #2]    ; R0 = 0x44444444   (address 0x2007C00C)

        ; ---- several registers at once ---------------------------------------------------------------
        MOV     R0, R1
        LDMIA   R0!, {R3-R6}            ; R3 = 0x11111111   R6 = 0x44444444   R0 = 0x2007C010
        ADD     R2, R1, #0x40           ; destination of a block copy: 0x2007C040
        MOV     R0, R1
        LDMIA   R0!, {R3-R6}            ; read 16 bytes ...
        STMIA   R2!, {R3-R6}            ; ... and write them: R2 = 0x2007C050
        LDR     R0, [R1, #0x4C]         ; R0 = 0x44444444   (last word of the copy)

        ; ---- practice ----------------------------------------------------------------------------
        MOV     R3, R1
        LDR     R0, [R3, #8]!           ; R0 = 0x33333333   R3 = 0x2007C008

        POP     {R4-R6, PC}
        END
