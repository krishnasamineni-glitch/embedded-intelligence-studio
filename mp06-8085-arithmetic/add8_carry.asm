;----------------------------------------------------------------------
; mp06  8085 arithmetic, program 1: 8-bit addition with carry
;
; Start address: 2000H
; Before:  [2050H] = 9AH   [2051H] = 87H
; After:   [2052H] = 21H (sum)   [2053H] = 01H (carry)      9AH + 87H = 121H
;----------------------------------------------------------------------
;        instruction     ; addr   code      comment
        LXI H, 2050H    ; 2000H  21 50 20  HL → first number
        MOV A, M        ; 2003H  7E        A = first number
        INX H           ; 2004H  23        HL → second number
        ADD M           ; 2005H  86        A = A + second
        INX H           ; 2006H  23        HL → 2052H
        MOV M, A        ; 2007H  77        store the sum
        MVI A, 00H      ; 2008H  3E 00     A = 0 (flags kept)
        ACI 00H         ; 200AH  CE 00     A = 0 + 0 + CY
        INX H           ; 200CH  23        HL → 2053H
        MOV M, A        ; 200DH  77        store the carry
        HLT             ; 200EH  76        stop
