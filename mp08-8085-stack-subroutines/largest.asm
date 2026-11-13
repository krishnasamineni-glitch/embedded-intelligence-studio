;----------------------------------------------------------------------
; mp08  8085 jumps and loops: the largest number in a list
;
; Start address: 2000H
; Before:  [2050H] = 05H (count)   2051H..2055H = 23H 8AH 45H 9CH 61H
; After:   [2060H] = 9CH (the largest)
; CMP M sets CY when A < M (unsigned), so JNC skips when A >= M.
;----------------------------------------------------------------------
;        instruction     ; addr   code      comment
        LXI H, 2050H    ; 2000H  21 50 20  HL → the list
        MOV C, M        ; 2003H  4E        C = count
        INX H           ; 2004H  23
        MOV A, M        ; 2005H  7E        A = first number
        DCR C           ; 2006H  0D        one number used
LOOP:   INX H           ; 2007H  23        next number
        CMP M           ; 2008H  BE        A − M, flags only
        JNC SKIP        ; 2009H  D2 0D 20  no carry: A ≥ M
        MOV A, M        ; 200CH  7E        new largest
SKIP:   DCR C           ; 200DH  0D
        JNZ LOOP        ; 200EH  C2 07 20  repeat
        STA 2060H       ; 2011H  32 60 20  store the result
        HLT             ; 2014H  76        stop
