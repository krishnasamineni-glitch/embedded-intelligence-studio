;----------------------------------------------------------------------
; mp05  8085 data transfer: swap two bytes in memory
;
; Start address: 2000H
; Before:  [2050H] = 11H   [2051H] = 22H
; After:   [2050H] = 22H   [2051H] = 11H     (flags unchanged)
;----------------------------------------------------------------------
;        instruction     ; addr   code      comment
        LDA 2050H       ; 2000H  3A 50 20  A = first byte
        MOV B, A        ; 2003H  47        keep it in B
        LDA 2051H       ; 2004H  3A 51 20  A = second byte
        STA 2050H       ; 2007H  32 50 20  second → first place
        MOV A, B        ; 200AH  78        A = first byte again
        STA 2051H       ; 200BH  32 51 20  first → second place
        HLT             ; 200EH  76        stop
