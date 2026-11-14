; programs_demo.s - the six complete programs (and the practice loop) of the "ARM assembly programs" video, ARM Cortex-M3 (Keil uVision).
; It uses the LPC1768 AHB SRAM at 0x2007C000 for its arrays (free in a normal Keil project).
; Call it from C:   extern void programs_demo(void);   programs_demo();
; Step through it in the debugger: compare each register with the comment.

        AREA    ProgramsDemo, CODE, READONLY
        THUMB
        EXPORT  programs_demo

programs_demo
        PUSH    {R4-R7, LR}

        ; ---- 1. the sum of an array of five words: 10 + 20 + 30 + 40 + 50 -----------------------
        LDR     R0, =0x2007C000         ; the array
        MOVS    R1, #10
        STR     R1, [R0]
        MOVS    R1, #20
        STR     R1, [R0, #4]
        MOVS    R1, #30
        STR     R1, [R0, #8]
        MOVS    R1, #40
        STR     R1, [R0, #12]
        MOVS    R1, #50
        STR     R1, [R0, #16]

        MOVS    R2, #0                  ; the sum
        MOVS    R3, #5                  ; the number of elements
sum_next
        LDR     R1, [R0], #4            ; the next element, then move the pointer on
        ADD     R2, R2, R1
        SUBS    R3, R3, #1
        BNE     sum_next
sum_end                                 ; R2 = 150

        ; ---- 2. the largest signed number of an array: 5, -3, 42, 17, -8 -------------------------
        LDR     R0, =0x2007C020
        MOVS    R1, #5
        STR     R1, [R0]
        MOV     R1, #-3
        STR     R1, [R0, #4]
        MOVS    R1, #42
        STR     R1, [R0, #8]
        MOVS    R1, #17
        STR     R1, [R0, #12]
        MOV     R1, #-8
        STR     R1, [R0, #16]

        LDR     R2, [R0], #4            ; the largest so far: the first element
        MOVS    R3, #4                  ; the elements still to check
max_next
        LDR     R1, [R0], #4
        CMP     R1, R2
        IT      GT
        MOVGT   R2, R1                  ; a larger one: keep it
        SUBS    R3, R3, #1
        BNE     max_next
max_end                                 ; R2 = 42

        ; ---- 3. count the 1 bits of a 32-bit word -----------------------------------------------
        LDR     R0, =0xF0F0F0F0
        MOVS    R1, #0                  ; the count
bits_next
        LSRS    R0, R0, #1              ; bit 0 goes into the carry flag
        ADC     R1, R1, #0              ; add the carry (ADC without S keeps the flags)
        BNE     bits_next               ; Z from LSRS: stop when no 1 bits are left
bits_end                                ; R1 = 16

        ; ---- 4. factorial: 10! ------------------------------------------------------------------
        MOVS    R0, #1                  ; the result
        MOVS    R1, #10
fact_next
        MUL     R0, R0, R1
        SUBS    R1, R1, #1
        BNE     fact_next
fact_end                                ; R0 = 0x00375F00   (3628800)

        ; ---- 5. the greatest common divisor of 48 and 18 (Euclid, by subtraction) ----------------
        MOVS    R0, #48
        MOVS    R1, #18
gcd_next
        CMP     R0, R1
        ITE     GT
        SUBGT   R0, R0, R1              ; R0 is larger: R0 = R0 - R1
        SUBLE   R1, R1, R0              ; R1 is larger or equal: R1 = R1 - R0
        BNE     gcd_next                ; the flags of CMP: repeat until R0 = R1
gcd_end                                 ; R0 = 6

        ; ---- 6. bubble sort of five signed words: 42, 7, -3, 19, 0 -------------------------------
        LDR     R0, =0x2007C040
        MOVS    R1, #42
        STR     R1, [R0]
        MOVS    R1, #7
        STR     R1, [R0, #4]
        MOV     R1, #-3
        STR     R1, [R0, #8]
        MOVS    R1, #19
        STR     R1, [R0, #12]
        MOVS    R1, #0
        STR     R1, [R0, #16]

        MOVS    R4, #4                  ; the number of passes
pass_next
        MOV     R5, R0                  ; a pointer to the first pair
        MOV     R6, R4                  ; the pairs to compare in this pass
pair_next
        LDR     R1, [R5]
        LDR     R2, [R5, #4]
        CMP     R1, R2
        ITT     GT
        STRGT   R2, [R5]                ; the pair is in the wrong order: swap it
        STRGT   R1, [R5, #4]
        ADDS    R5, R5, #4
        SUBS    R6, R6, #1
        BNE     pair_next
        SUBS    R4, R4, #1
        BNE     pass_next
sort_end
        LDM     R0, {R1, R2, R3, R6, R7} ; R1 = 0xFFFFFFFD   R2 = 0   R3 = 7   R6 = 19   R7 = 42

        ; ---- practice: what does this loop compute? ----------------------------------------------
        MOVS    R0, #0
        MOVS    R1, #1
sum100_next
        ADD     R0, R0, R1
        ADD     R1, R1, #1
        CMP     R1, #101
        BNE     sum100_next
sum100_end                              ; R0 = 5050   (1 + 2 + ... + 100)

        POP     {R4-R7, PC}
        END
