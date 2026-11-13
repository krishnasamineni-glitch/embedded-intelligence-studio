; ----------------------------------------------------------------------
; mp19  8086 interrupts: install your own interrupt service routine
; as type 60H, call it with INT 60H.          MASM / TASM / EMU8086
;
; Vector of type n is at n x 4:  60H x 4 = 180H  ->  0000:0180H
;   0000:0180H = offset  (new IP)
;   0000:0182H = segment (new CS)
; ----------------------------------------------------------------------
DATA SEGMENT
    MSG    DB 'Hello from MYISR (type 60H)', 13, 10, '$'
    OLD_IP DW ?
    OLD_CS DW ?
DATA ENDS

CODE SEGMENT
    ASSUME CS:CODE, DS:DATA
START:
    MOV AX, DATA
    MOV DS, AX

    MOV AX, 0
    MOV ES, AX                               ; ES -> the vector table

    MOV AX, ES:[180H]                        ; save the old vector
    MOV OLD_IP, AX                           ; (a good habit)
    MOV AX, ES:[182H]
    MOV OLD_CS, AX

    MOV WORD PTR ES:[180H], OFFSET MYISR     ; new IP
    MOV WORD PTR ES:[182H], SEG MYISR        ; new CS

    INT 60H                                  ; runs MYISR
    INT 60H                                  ; ... as often as we like

    MOV AX, OLD_IP                           ; put the old vector back
    MOV ES:[180H], AX
    MOV AX, OLD_CS
    MOV ES:[182H], AX

    MOV AH, 4CH                              ; back to DOS
    INT 21H

; INT 60H pushes FLAGS, CS and IP, clears IF and TF, and jumps here.
MYISR PROC FAR
    PUSH AX                                  ; save what we use
    PUSH DX
    MOV DX, OFFSET MSG                       ; DS still points to DATA
    MOV AH, 09H                              ; DOS: print text up to '$'
    INT 21H
    POP DX
    POP AX
    IRET                                     ; pops IP, CS and FLAGS
MYISR ENDP

CODE ENDS
    END START
