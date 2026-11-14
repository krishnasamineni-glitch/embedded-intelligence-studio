; cabi_demo.s - the examples of the "C and assembly together" video, ARM Cortex-M3 (Keil uVision, ARM assembler).
; max2, mul64 and sum5 follow the ARM procedure call standard (AAPCS), so C can call them directly:
;     extern int max2(int a, int b);
;     extern unsigned long long mul64(unsigned a, unsigned b);
;     extern int sum5(int a, int b, int c, int d, int e);
; cabi_demo calls all three from assembly; step through it and compare each register with the comment.

        AREA    CAbiDemo, CODE, READONLY
        THUMB
        EXPORT  cabi_demo
        EXPORT  max2
        EXPORT  mul64
        EXPORT  sum5

cabi_demo
        PUSH    {R4, LR}                ; two registers: the stack stays aligned to 8 bytes
        LDR     R0, =0xFFFFFFFB         ; a = -5
        MOVS    R1, #3                  ; b = 3
        BL      max2                    ; R0 = 3
        LDR     R0, =0x00010000
        LDR     R1, =0x00010000
        BL      mul64                   ; R0 = 0x00000000   R1 = 0x00000001   (the product is 0x0000000100000000)
        SUB     SP, SP, #8              ; room for the fifth argument (8 bytes keep the stack aligned)
        MOVS    R4, #5
        STR     R4, [SP]                ; the fifth argument goes on the stack
        MOVS    R0, #1
        MOVS    R1, #2
        MOVS    R2, #3
        MOVS    R3, #4
        BL      sum5                    ; R0 = 15
        ADD     SP, SP, #8
        POP     {R4, PC}

; ---- the three functions, exactly as a compiler makes them (clang -Os for Cortex-M3) ------------------
max2                                    ; R0 = a, R1 = b  ->  R0 = the larger one (signed)
        CMP     R0, R1
        IT      LE
        MOVLE   R0, R1
        BX      LR

mul64                                   ; R0 = a, R1 = b  ->  R1:R0 = a x b, all 64 bits
        UMULL   R0, R1, R1, R0
        BX      LR

sum5                                    ; R0 .. R3 = a .. d, the word at SP = e  ->  R0 = a + b + c + d + e
        ADD     R0, R0, R1
        LDR     R12, [SP]               ; the fifth argument
        ADD     R0, R0, R2
        ADD     R0, R0, R3
        ADD     R0, R0, R12
        BX      LR

        END
