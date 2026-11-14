; shifts_demo.s - the examples of the "shifts, rotates and barrel shifter" video, ARM Cortex-M3 (Keil, ARM assembler).
; Call it from C:   extern void shifts_demo(void);   shifts_demo();
; Step through it in the debugger and compare each register with the value in the comment.

        AREA    ShiftsDemo, CODE, READONLY
        THUMB
        EXPORT  shifts_demo

shifts_demo
        PUSH    {R4, LR}

        MOVS    R0, #0x0F
        LSLS    R1, R0, #4              ; R1 = 0x000000F0   (15 x 16 = 240), C = 0

        LDR     R0, =0x40000000
        LSLS    R1, R0, #1              ; R1 = 0x80000000   positive became negative (signed)
        LSLS    R1, R0, #2              ; R1 = 0x00000000   C = 1: the 1 fell out

        MOVS    R0, #0xF0
        LSRS    R1, R0, #4              ; R1 = 0x0000000F   (240 / 16 = 15)

        MVN     R0, #7                  ; R0 = 0xFFFFFFF8   (-8)
        LSRS    R1, R0, #1              ; R1 = 0x7FFFFFFC   LSR loses the sign
        ASRS    R1, R0, #1              ; R1 = 0xFFFFFFFC   (-4)  ASR keeps the sign

        MVN     R0, #6                  ; R0 = 0xFFFFFFF9   (-7)
        ASRS    R1, R0, #1              ; R1 = 0xFFFFFFFC   (-4): ASR rounds down, C = 1

        LDR     R0, =0x12345678
        RORS    R1, R0, #8              ; R1 = 0x78123456   C = 0 (new bit 31)
        ROR     R1, R0, #24             ; R1 = 0x34567812   = rotate LEFT by 8

        MOVS    R0, #3
        MOVS    R4, #0
        LSRS    R4, R4, #1              ; makes C = 0 (0 shifted right: bit 0 = 0 goes into C)
        RRXS    R1, R0                  ; R1 = 0x00000001   C = 1 (old bit 0)

        ; 64-bit value in R3:R2 shifted right by one
        LDR     R3, =0x00000001         ; high word
        LDR     R2, =0x00000000         ; low word
        LSRS    R3, R3, #1              ; R3 = 0x00000000, C = 1
        RRX     R2, R2                  ; R2 = 0x80000000

        ; barrel shifter
        LDR     R1, =0x10000000         ; start of an array of words
        MOVS    R2, #3                  ; index
        ADD     R0, R1, R2, LSL #2      ; R0 = 0x1000000C: address of element 3

        MOVS    R0, #6
        ADD     R1, R0, R0, LSL #2      ; R1 = 30 (5 x 6)
        RSB     R2, R0, R0, LSL #3      ; R2 = 42 (7 x 6)

        LDR     R0, =0xFFFFFFF0         ; practice: -16
        LSRS    R1, R0, #2              ; R1 = 0x3FFFFFFC
        ASRS    R2, R0, #2              ; R2 = 0xFFFFFFFC (-4)

        POP     {R4, PC}
        END
