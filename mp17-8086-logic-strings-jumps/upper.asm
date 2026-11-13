; ----------------------------------------------------------------------
; mp17  8086 strings and jumps: copy a text, small letters -> capitals
; MASM / TASM / EMU8086
;
; Same instructions as in the video. The fixed addresses of the kit
; version (0500H, 0600H) are replaced by the names TEXT and RESULT.
; Result: RESULT = 'HI 86'   (printed on the screen at the end)
; ----------------------------------------------------------------------
DATA SEGMENT
    TEXT   DB 'Hi 86'              ; the source text
    RESULT DB 5 DUP (?), '$'       ; the copy; '$' ends the text for printing
DATA ENDS

CODE SEGMENT
    ASSUME CS:CODE, DS:DATA, ES:DATA
START:
    MOV AX, DATA
    MOV DS, AX              ; LODSB reads from DS:SI
    MOV ES, AX              ; STOSB writes to ES:DI
    MOV SI, OFFSET TEXT     ; source           (kit: MOV SI, 0500H)
    MOV DI, OFFSET RESULT   ; destination      (kit: MOV DI, 0600H)
    MOV CX, 0005H           ; 5 characters
    CLD                     ; forward: SI and DI count up
NEXT:
    LODSB                   ; AL = character, SI = SI + 1
    CMP AL, 'a'
    JB STORE                ; below 'a': not a small letter
    CMP AL, 'z'
    JA STORE                ; above 'z': not a small letter
    SUB AL, 20H             ; small -> capital (69H 'i' -> 49H 'I')
STORE:
    STOSB                   ; store AL, DI = DI + 1
    LOOP NEXT               ; CX = CX - 1, repeat while CX > 0

    MOV DX, OFFSET RESULT   ; show the result (DOS function 09H)
    MOV AH, 09H
    INT 21H
    MOV AH, 4CH             ; back to DOS      (kit: HLT)
    INT 21H
CODE ENDS
    END START
