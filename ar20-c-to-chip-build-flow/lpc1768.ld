/* lpc1768.ld - where everything goes: flash at 0x00000000, the local SRAM at 0x10000000 */
ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x10000000, LENGTH = 32K
}
_estack = ORIGIN(RAM) + LENGTH(RAM);        /* 0x10008000: the stack starts at the top of RAM */

SECTIONS
{
    .text : {
        KEEP(*(.isr_vector))                    /* the vector table must be first, at address 0 */
        *(.text*)
        *(.rodata*)
    } > FLASH
    _sidata = LOADADDR(.data);
    .data : { _sdata = .; *(.data*) _edata = .; } > RAM AT > FLASH
    .bss  : { _sbss = .;  *(.bss*) *(COMMON) _ebss = .; } > RAM
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) }
}
