; arith_demo.s - the examples of the "arithmetic instructions" video, ARM Cortex-M3 (Keil uVision, ARM assembler).
; Call it from C:   extern void arith_demo(void);   arith_demo();
; Step through it in the debugger and compare each register with the value in the comment.

        AREA    ArithDemo, CODE, READONLY
        THUMB
        EXPORT  arith_demo

arith_demo
        PUSH    {R4-R7, LR}

        ; ---- MOV and MVN -----------------------------------------------------------------
        MOVS    R1, #42                 ; R1 = 0x0000002A
        MOV     R0, R1                  ; R0 = 0x0000002A   (a copy)
        MVN     R0, #0                  ; R0 = 0xFFFFFFFF   (NOT 0)
        MVN     R0, R1                  ; R0 = 0xFFFFFFD5   (NOT 42 = -43)

        ; ---- ADD -----------------------------------------------------------------------------
        MOVS    R1, #25
        MOVS    R2, #17
        ADD     R0, R1, R2              ; R0 = 0x0000002A   (25 + 17 = 42)
        ADD     R0, R1, #100            ; R0 = 0x0000007D   (125)
        ADD     R0, R0, #1              ; R0 = 0x0000007E   (126)

        ; ---- 64-bit addition: R1:R0 + R3:R2 -> R5:R4 ------------------------------------------
        LDR     R0, =0xFFFFFFFF         ; low word of 0x00000001_FFFFFFFF
        MOVS    R1, #1                  ; high word
        MOVS    R2, #1                  ; low word of 0x00000000_00000001
        MOVS    R3, #0                  ; high word
        ADDS    R4, R0, R2              ; R4 = 0x00000000   C = 1
        ADC     R5, R1, R3              ; R5 = 0x00000002   (1 + 0 + C)

        ; ---- SUB and RSB ---------------------------------------------------------------------
        MOVS    R1, #50
        MOVS    R2, #8
        SUB     R0, R1, R2              ; R0 = 0x0000002A   (50 - 8 = 42)
        MOVS    R1, #5
        RSB     R0, R1, #0              ; R0 = 0xFFFFFFFB   (0 - 5 = -5)
        RSB     R0, R1, #100            ; R0 = 0x0000005F   (100 - 5 = 95)

        ; ---- 64-bit subtraction: R5:R4 - 1 -----------------------------------------------------
        MOVS    R2, #1
        MOVS    R3, #0
        SUBS    R6, R4, R2              ; R6 = 0xFFFFFFFF   C = 0 (borrow)
        SBC     R7, R5, R3              ; R7 = 0x00000001   (2 - 0 - borrow)

        ; ---- multiply --------------------------------------------------------------------------
        MOV     R1, #1000
        MOV     R2, #3000
        MUL     R0, R1, R2              ; R0 = 0x002DC6C0   (3,000,000)
        MOVS    R3, #10
        MLA     R0, R1, R2, R3          ; R0 = 0x002DC6CA   (10 + 1000 x 3000)
        MLS     R0, R3, R3, R2          ; R0 = 0x00000B54   (3000 - 10 x 10 = 2900)

        ; ---- long multiply -----------------------------------------------------------------------
        MOV     R1, #0x10000
        MOV     R2, #0x10000
        MUL     R0, R1, R2              ; R0 = 0x00000000   (the 1 at bit 32 is lost)
        UMULL   R4, R5, R1, R2          ; R4 = 0x00000000   R5 = 0x00000001   (64-bit result)
        MVN     R1, #1                  ; R1 = 0xFFFFFFFE   (-2)
        MOVS    R2, #3
        SMULL   R4, R5, R1, R2          ; R4 = 0xFFFFFFFA   R5 = 0xFFFFFFFF   (-6 as 64 bits)

        ; ---- divide ----------------------------------------------------------------------------
        MOVS    R1, #100
        MOVS    R2, #7
        UDIV    R0, R1, R2              ; R0 = 0x0000000E   (100 / 7 = 14)
        MLS     R3, R0, R2, R1          ; R3 = 0x00000002   (remainder: 100 - 14 x 7)
        MVN     R1, #6                  ; R1 = 0xFFFFFFF9   (-7)
        MOVS    R2, #2
        SDIV    R0, R1, R2              ; R0 = 0xFFFFFFFD   (-7 / 2 = -3, rounds towards zero)
        MOVS    R2, #0
        UDIV    R0, R1, R2              ; R0 = 0x00000000   (divide by 0 gives 0, unless DIV_0_TRP is set)

        ; ---- practice ----------------------------------------------------------------------------
        MOVS    R1, #50
        MOVS    R2, #8
        UDIV    R0, R1, R2              ; R0 = 0x00000006
        MLS     R3, R0, R2, R1          ; R3 = 0x00000002

        POP     {R4-R7, PC}
        END
