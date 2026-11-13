; ----------------------------------------------------------------------
; mp18  a complete 8086 program: the largest number in an array
; MASM / TASM / EMU8086          Result: LARGEST = 9CH
; ----------------------------------------------------------------------
DATA SEGMENT
    NUMS    DB 23H, 8AH, 45H, 9CH, 61H
    COUNT   EQU 5
    LARGEST DB ?
DATA ENDS
CODE SEGMENT
    ASSUME CS:CODE, DS:DATA
START:
    MOV AX, DATA
    MOV DS, AX
    LEA SI, NUMS
    MOV CX, COUNT
    MOV AL, [SI]   ; largest so far
    DEC CX
NEXT:
    INC SI
    CMP AL, [SI]
    JAE SKIP
    MOV AL, [SI]   ; new largest
SKIP:
    LOOP NEXT
    MOV LARGEST, AL
    MOV AH, 4CH
    INT 21H
CODE ENDS
    END START
