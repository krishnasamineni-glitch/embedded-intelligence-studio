; add3.s - the complete Keil assembly file of the "instruction set basics" video, ARM Cortex-M3.
; C calls it as:   extern int add3(int a, int b, int c);   int x = add3(10, 20, 12);   // x = 42
; The arguments arrive in R0, R1 and R2, and the result goes back in R0 (ARM procedure call standard).

        AREA    MyCode, CODE, READONLY
        THUMB
        EXPORT  add3

add3                                    ; R0 = R0 + R1 + R2
        ADDS    R0, R0, R1
        ADDS    R0, R0, R2
        BX      LR

        END
