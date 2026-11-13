; ----------------------------------------------------------------------
; mp18  skeleton of every 8086 program (MASM / TASM / EMU8086)
; ----------------------------------------------------------------------
DATA SEGMENT
    ; data here, for example:
    ;   NUMS  DB 23H, 8AH, 45H
    ;   TOTAL DW ?
    ;   BUF   DB 10 DUP (0)
    ;   MSG   DB 'HI$'
DATA ENDS

CODE SEGMENT
    ASSUME CS:CODE, DS:DATA
START:
    MOV AX, DATA        ; a segment register cannot take a value directly,
    MOV DS, AX          ; so DS is loaded through AX

    ; instructions here

    MOV AH, 4CH         ; return to DOS
    INT 21H
CODE ENDS
    END START
