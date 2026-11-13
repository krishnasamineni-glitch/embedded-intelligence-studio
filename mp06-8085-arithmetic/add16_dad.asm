;----------------------------------------------------------------------
; mp06  8085 arithmetic, program 2: 16-bit addition with DAD
;
; Start address: 2000H   (numbers are stored low byte first)
; Before:  [2050H] = 34H [2051H] = 12H  (1234H)   [2052H] = 11H [2053H] = 11H  (1111H)
; After:   [2054H] = 45H [2055H] = 23H  (2345H)   CY = carry out of bit 15
;----------------------------------------------------------------------
;        instruction     ; addr   code      comment
        LHLD 2050H      ; 2000H  2A 50 20  HL = first number
        XCHG            ; 2003H  EB        DE = first number
        LHLD 2052H      ; 2004H  2A 52 20  HL = second number
        DAD D           ; 2007H  19        HL = HL + DE
        SHLD 2054H      ; 2008H  22 54 20  store the result
        HLT             ; 200BH  76        stop
