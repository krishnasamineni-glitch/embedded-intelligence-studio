; system_demo.s - the examples of the "special and system instructions" video, ARM Cortex-M3 (Keil uVision).
; It must run in privileged thread mode (the normal state after reset, in a project without an RTOS).
; It uses the LPC1768 AHB SRAM at 0x2007C000 as a scratch word.
; Call it from C:   extern void system_demo(void);   system_demo();
; Step through it in the debugger: compare each register with the comment.

        AREA    SystemDemo, CODE, READONLY
        THUMB
        EXPORT  system_demo
        EXPORT  SVC_Handler

system_demo
        PUSH    {R4-R7, LR}

        ; ---- MRS: read the flags into a register -------------------------------------------------
        LDR     R0, =0x7FFFFFFF         ; the largest positive 32-bit number
        ADDS    R0, R0, #1              ; flags: N=1 Z=0 C=0 V=1
        MRS     R3, APSR                ; R3 = 0x90000000   (N and V are bits 31 and 28)
        CMP     R0, R0                  ; flags: N=0 Z=1 C=1 V=0
        MRS     R4, APSR                ; R4 = 0x60000000   (practice: Z and C)

        ; ---- MSR: write the flags directly --------------------------------------------------------
        LDR     R1, =0x20000000         ; only C set
        MSR     APSR_nzcvq, R1          ; flags: N=0 Z=0 C=1 V=0

        ; ---- PRIMASK: all interrupts off and on again ----------------------------------------------
        CPSID   I                       ; PRIMASK = 1
        MRS     R5, PRIMASK             ; R5 = 1
        CPSIE   I                       ; PRIMASK = 0
        MRS     R6, PRIMASK             ; R6 = 0

        ; ---- BASEPRI: block only the less urgent interrupts --------------------------------------
        MOVS    R0, #0x40               ; on the LPC1768 (5 priority bits) this is priority 8
        MSR     BASEPRI, R0             ; priorities 8 .. 31 are blocked, 0 .. 7 still run
        MRS     R7, BASEPRI             ; R7 = 0x00000040
        MOVS    R0, #0
        MSR     BASEPRI, R0             ; 0 = no masking

        ; ---- an atomic increment with LDREX and STREX -------------------------------------------
        LDR     R1, =0x2007C000
        MOVS    R2, #41
        STR     R2, [R1]
retry
        LDREX   R0, [R1]                ; read, and mark the address for exclusive access
        ADDS    R0, R0, #1
        STREX   R2, R0, [R1]            ; store only if nothing else touched it: R2 = 0 means success
        CMP     R2, #0
        BNE     retry                   ; R2 is 1 when someone else was faster: try again
inc_done                                ; R0 = 42   R2 = 0

        ; ---- barriers: harmless here, required after some system changes ------------------------
        DSB                             ; finish all memory accesses
        ISB                             ; refetch the following instructions

        POP     {R4-R7, PC}

; ---- SVC_Handler: find the number of the SVC instruction that called it ----------------------------
; (the processor runs it when an SVC #n is executed; it is not run by system_demo above)
SVC_Handler
        TST     LR, #4                  ; EXC_RETURN bit 2: which stack holds the frame?
        ITE     EQ
        MRSEQ   R0, MSP
        MRSNE   R0, PSP
        LDR     R1, [R0, #24]           ; the stacked PC: the address after the SVC instruction
        LDRB    R0, [R1, #-2]           ; the low byte of the SVC instruction is its number n
        BX      LR                      ; (a real handler would now do service n)

        END
