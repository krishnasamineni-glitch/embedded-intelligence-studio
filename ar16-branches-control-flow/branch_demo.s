; branch_demo.s - the examples of the "branches and control flow" video, ARM Cortex-M3 (Keil uVision, ARM assembler).
; It uses the LPC1768 AHB SRAM at 0x2007C000 as a scratch area (free in a normal Keil project).
; Call it from C:   extern void branch_demo(void);   branch_demo();
; Step through it in the debugger: compare each register with the comment.

        AREA    BranchDemo, CODE, READONLY
        THUMB
        EXPORT  branch_demo

branch_demo
        PUSH    {R4, LR}

        ; ---- signed and unsigned conditions: 0xFFFFFFFF compared with 1 ------------------------------
        LDR     R0, =0xFFFFFFFF         ; -1 as a signed number, 4294967295 as an unsigned number
        MOVS    R1, #1
        MOVS    R2, #0
        MOVS    R3, #0
        CMP     R0, R1                  ; flags: N=1 Z=0 C=1 V=0
        BLS     not_higher              ; unsigned: 0xFFFFFFFF is higher than 1, so no branch
        MOVS    R2, #1
not_higher
        CMP     R0, R1
        BLE     not_greater             ; signed: -1 is not greater than 1, so this branch is taken
        MOVS    R3, #1                  ; (skipped)
not_greater                             ; R2 = 1   R3 = 0

        ; ---- if / else with branches: R2 = the larger signed number --------------------------------
        LDR     R0, =0xFFFFFFFB         ; -5
        MOVS    R1, #3
        CMP     R0, R1
        BLT     use_r1
        MOV     R2, R0
        B       max_done
use_r1
        MOV     R2, R1
max_done                                ; R2 = 3

        ; ---- the same if / else with an IT block: no branch at all ------------------------------
        MOVS    R2, #0
        CMP     R0, R1
        ITE     GE
        MOVGE   R2, R0
        MOVLT   R2, R1                  ; R2 = 3

        ; ---- a counting loop: 10 + 9 + ... + 1 ---------------------------------------------------
        MOVS    R0, #0                  ; the sum
        MOVS    R1, #10                 ; the counter
sum_loop
        ADDS    R0, R0, R1
        SUBS    R1, R1, #1              ; sets Z when the counter reaches 0
        BNE     sum_loop
sum_done                                ; R0 = 55   R1 = 0

        ; ---- CBZ: the length of a zero-terminated string ----------------------------------------
        LDR     R0, =0x2007C000
        LDR     R1, =0x004D5241         ; the bytes 'A' 'R' 'M' 0, little endian
        STR     R1, [R0]
        MOVS    R1, #0                  ; the length so far
next_char
        LDRB    R2, [R0, R1]
        CBZ     R2, str_end             ; stop at the zero byte
        ADDS    R1, R1, #1
        B       next_char
str_end                                 ; R1 = 3

        ; ---- functions: BL saves the return address in LR ---------------------------------------
        MOVS    R0, #7
        BL      square                  ; R0 = 49
        MOVS    R0, #3
        MOVS    R1, #4
        BL      sumsq                   ; R0 = 25

        ; ---- a switch with a table branch ---------------------------------------------------------
        MOVS    R0, #2                  ; the case number
        TBB     [PC, R0]
sw_table
        DCB     (case0 - sw_table) / 2
        DCB     (case1 - sw_table) / 2
        DCB     (case2 - sw_table) / 2
        ALIGN   2
case0
        MOVS    R1, #10
        B       sw_done
case1
        MOVS    R1, #20
        B       sw_done
case2
        MOVS    R1, #30
sw_done                                 ; R1 = 30

        ; ---- practice: what is R0 at the end? ----------------------------------------------------
        MOVS    R0, #1
        MOVS    R1, #5
pow_loop
        LSLS    R0, R0, #1
        SUBS    R1, R1, #1
        BNE     pow_loop
pow_done                                ; R0 = 32

        POP     {R4, PC}

; ---- square: R0 = R0 x R0 (a leaf function: it calls nothing, so LR can stay in LR) -------------
square
        MULS    R0, R0, R0
        BX      LR

; ---- sumsq: R0 = a, R1 = b  ->  R0 = a x a + b x b (it calls square, so it saves LR first) -------
sumsq
        PUSH    {R4, LR}
        MOV     R4, R0                  ; R4 = a
        MOV     R0, R1
        BL      square                  ; R0 = 16
        MOV     R1, R4                  ; R1 = a
        MOV     R4, R0                  ; R4 = b x b
        MOV     R0, R1
        BL      square                  ; R0 = 9
        ADD     R0, R0, R4              ; R0 = 25
        POP     {R4, PC}

        END
