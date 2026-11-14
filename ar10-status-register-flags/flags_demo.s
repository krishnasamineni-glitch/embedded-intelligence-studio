; flags_demo.s - the cases of the "status register" video, for an ARM Cortex-M3 (Keil uVision, ARM assembler).
; Call it from C:   extern void flags_demo(void);   flags_demo();
; Step through it in the debugger (F11) and watch N, Z, C and V in the xPSR register after each line marked "flags".

        AREA    FlagsDemo, CODE, READONLY
        THUMB
        EXPORT  flags_demo

flags_demo
        PUSH    {R4, LR}

        ; ---- addition --------------------------------------------------------------
        MOVS    R0, #5                  ; case 1: 5 + 3 = 8
        MOVS    R1, #3
        ADDS    R2, R0, R1              ; flags: N=0 Z=0 C=0 V=0   R2 = 0x00000008

        LDR     R0, =0x7FFFFFFF         ; case 2: largest positive + 1
        MOVS    R1, #1
        ADDS    R2, R0, R1              ; flags: N=1 Z=0 C=0 V=1   R2 = 0x80000000 (signed overflow)

        LDR     R0, =0xFFFFFFFF         ; case 3: -1 + 1 (unsigned: 4294967295 + 1)
        MOVS    R1, #1
        ADDS    R2, R0, R1              ; flags: N=0 Z=1 C=1 V=0   R2 = 0x00000000 (unsigned overflow)

        LDR     R0, =0x80000000         ; case 4: most negative + most negative
        MOV     R1, R0
        ADDS    R2, R0, R1              ; flags: N=0 Z=1 C=1 V=1   R2 = 0x00000000 (both wrong)

        ; ---- subtraction: C = 1 means NO borrow -------------------------------------
        MOVS    R0, #5                  ; case 5: 5 - 3
        MOVS    R1, #3
        SUBS    R2, R0, R1              ; flags: N=0 Z=0 C=1 V=0   R2 = 0x00000002

        MOVS    R0, #3                  ; case 6: 3 - 5 (a borrow)
        MOVS    R1, #5
        SUBS    R2, R0, R1              ; flags: N=1 Z=0 C=0 V=0   R2 = 0xFFFFFFFE (-2)

        MOVS    R0, #5                  ; case 7: 5 - 5
        MOVS    R1, #5
        SUBS    R2, R0, R1              ; flags: N=0 Z=1 C=1 V=0   R2 = 0x00000000

        LDR     R0, =0x80000000         ; case 8: most negative - 1
        MOVS    R1, #1
        SUBS    R2, R0, R1              ; flags: N=0 Z=0 C=1 V=1   R2 = 0x7FFFFFFF (signed overflow)

        ; ---- one compare, two meanings ----------------------------------------------
        MOVS    R3, #0                  ; (clear R3 and R4 first: MOVS also changes the flags)
        MOVS    R4, #0
        LDR     R0, =0xFFFFFFFF         ; unsigned 4294967295, signed -1
        MOVS    R1, #1
        CMP     R0, R1                  ; flags: N=1 Z=0 C=1 V=0
        IT      HI                      ; unsigned: R0 > R1 ?  (HI: C=1 and Z=0)
        MOVHI   R3, #1                  ; yes -> R3 = 0x00000001
        IT      LT                      ; signed: R0 < R1 ?    (LT: N not equal to V)
        MOVLT   R4, #1                  ; yes -> R4 = 0x00000001

        ; ---- practice ------------------------------------------------------------------
        LDR     R1, =0x40000000
        MOV     R2, R1
        ADDS    R0, R1, R2              ; flags: N=1 Z=0 C=0 V=1   R0 = 0x80000000

        POP     {R4, PC}
        END
