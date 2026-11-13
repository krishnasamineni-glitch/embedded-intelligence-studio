;----------------------------------------------------------------------
; mp10  8085 interrupts: count RST 7.5 pulses
;
; Main program at 2000H, vector at 003CH, interrupt service routine (ISR) at 2100H.
; Every rising edge on the RST 7.5 pin adds 1 to the counter at 2050H.
; MVI A, 0BH = 0000 1011: MSE = 1, RST 6.5 and 5.5 masked, only RST 7.5 enabled.
;----------------------------------------------------------------------
;        instruction     ; addr   code      comment

; ---- main program
        LXI SP, 2FFFH   ; 2000H  31 FF 2F  stack
        MVI A, 0BH      ; 2003H  3E 0B     only RST 7.5
        SIM             ; 2005H  30
        EI              ; 2006H  FB
LOOP:   JMP LOOP        ; 2007H  C3 07 20  wait

; ---- RST 7.5 vector (003CH)
        JMP 2100H       ; 003CH  C3 00 21  to the ISR

; ---- interrupt service routine
        PUSH PSW        ; 2100H  F5        save A + flags
        PUSH H          ; 2101H  E5        save HL
        LXI H, 2050H    ; 2102H  21 50 20
        INR M           ; 2105H  34        count
        POP H           ; 2106H  E1        restore
        POP PSW         ; 2107H  F1
        EI              ; 2108H  FB
        RET             ; 2109H  C9        back
