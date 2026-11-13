; ----------------------------------------------------------------------
; mp16  8086 data transfer + arithmetic: add five bytes, 16-bit sum
; MASM / TASM / EMU8086
;
; Same instructions as in the video. The fixed addresses of the kit
; version (0500H, 0600H) are replaced by the names ARRAY and SUM.
; Result: SUM = 020FH (= 527)
; ----------------------------------------------------------------------
DATA SEGMENT
    ARRAY DB 7FH, 80H, 0FFH, 10H, 01H   ; the five bytes from the video
    SUM   DW ?                          ; the 16-bit sum goes here
DATA ENDS

CODE SEGMENT
    ASSUME CS:CODE, DS:DATA
START:
    MOV AX, DATA
    MOV DS, AX
    MOV SI, OFFSET ARRAY   ; SI -> the array     (kit: MOV SI, 0500H)
    MOV CX, 0005H          ; count
    MOV AX, 0000H          ; sum = 0
NEXT:
    ADD AL, [SI]           ; add a byte
    ADC AH, 00H            ; add the carry into AH
    INC SI                 ; next byte
    DEC CX                 ; count down
    JNZ NEXT               ; repeat until CX = 0
    MOV SUM, AX            ; store the sum       (kit: MOV [0600H], AX)
    MOV AH, 4CH            ; back to DOS        (kit: HLT)
    INT 21H
CODE ENDS
    END START
