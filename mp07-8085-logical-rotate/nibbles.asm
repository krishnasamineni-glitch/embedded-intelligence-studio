;----------------------------------------------------------------------
; mp07  8085 logical + rotate: split a byte into its two nibbles
;
; Start address: 2000H
; Before:  [2050H] = A7H
; After:   [2051H] = 07H (lower nibble)   [2052H] = 0AH (upper nibble)
;----------------------------------------------------------------------
;        instruction     ; addr   code      comment
        LDA 2050H       ; 2000H  3A 50 20  A = A7H
        ANI 0FH         ; 2003H  E6 0F     keep the lower nibble
        STA 2051H       ; 2005H  32 51 20  store 07H
        LDA 2050H       ; 2008H  3A 50 20  A = A7H again
        ANI F0H         ; 200BH  E6 F0     keep the upper nibble
        RRC             ; 200DH  0F
        RRC             ; 200EH  0F
        RRC             ; 200FH  0F
        RRC             ; 2010H  0F        4 × right
        STA 2052H       ; 2011H  32 52 20  store 0AH
        HLT             ; 2014H  76        stop
