; logic_demo.s - the examples of the "logic and bit manipulation" video, ARM Cortex-M3 (Keil uVision, ARM assembler).
; Call it from C:   extern void logic_demo(void);   logic_demo();
; Step through it in the debugger and compare each register with the value in the comment.

        AREA    LogicDemo, CODE, READONLY
        THUMB
        EXPORT  logic_demo

logic_demo
        PUSH    {R4, LR}

        LDR     R0, =0x12345678

        ; ---- AND, ORR, EOR, BIC, ORN -------------------------------------------------------
        AND     R1, R0, #0xFF           ; R1 = 0x00000078   keep only the low byte (a mask)
        ORR     R1, R0, #0x80000000     ; R1 = 0x92345678   set bit 31
        BIC     R1, R0, #0xF0           ; R1 = 0x12345608   clear bits 7..4
        EOR     R1, R0, #0xFF           ; R1 = 0x12345687   toggle bits 7..0
        ORN     R1, R0, #0xFF           ; R1 = 0xFFFFFF78   R0 OR NOT 0xFF

        ; ---- one bit of a GPIO-style register: set, clear, toggle -----------------------------
        MOVS    R2, #0
        ORR     R2, R2, #0x00400000     ; R2 = 0x00400000   set bit 22
        EOR     R2, R2, #0x00400000     ; R2 = 0x00000000   toggle bit 22 (now 0)
        ORR     R2, R2, #0x00400000     ; R2 = 0x00400000
        BIC     R2, R2, #0x00400000     ; R2 = 0x00000000   clear bit 22

        ; ---- test and compare: flags only ----------------------------------------------------
        TST     R0, #0x80               ; flags: N=0 Z=1 C=0 V=0   bit 7 of 0x12345678 is 0
        TST     R0, #0x40               ; flags: N=0 Z=0 C=0 V=0   bit 6 is 1
        TEQ     R0, R0                  ; flags: N=0 Z=1 C=0 V=0   equal values
        MVN     R3, #4                  ; R3 = 0xFFFFFFFB   (-5)
        MOVS    R4, #5
        CMN     R4, R3                  ; flags: N=0 Z=1 C=1 V=0   5 + (-5) = 0

        ; ---- bit fields -----------------------------------------------------------------------
        UBFX    R1, R0, #8, #4          ; R1 = 0x00000006   bits 11..8 of 0x12345678
        MOVS    R2, #0xF0
        SBFX    R1, R2, #4, #4          ; R1 = 0xFFFFFFFF   bits 7..4 = 1111, sign-extended: -1
        MOV     R1, R0
        MOVS    R2, #0x0A
        BFI     R1, R2, #8, #4          ; R1 = 0x12345A78   insert 0xA into bits 11..8
        MOV     R1, R0
        BFC     R1, #0, #8              ; R1 = 0x12345600   clear bits 7..0

        ; ---- counting and reversing -----------------------------------------------------------
        MOV     R2, #0x10000
        CLZ     R1, R2                  ; R1 = 0x0000000F   15 leading zeros
        MOVS    R2, #1
        RBIT    R1, R2                  ; R1 = 0x80000000   bits reversed
        REV     R1, R0                  ; R1 = 0x78563412   bytes reversed (endianness)
        REV16   R1, R0                  ; R1 = 0x34127856   bytes swapped in each halfword

        ; ---- practice -------------------------------------------------------------------------
        LDR     R0, =0xABCD1234
        UBFX    R1, R0, #16, #8         ; R1 = 0x000000CD
        BIC     R2, R0, #0xFF000000     ; R2 = 0x00CD1234

        POP     {R4, PC}
        END
