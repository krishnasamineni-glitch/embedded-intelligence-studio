/* startup.c - the smallest startup code for the LPC1768 (ARM Cortex-M3), written in C.
   The vector table, the Reset_Handler that prepares RAM, and default handlers. */
#include <stdint.h>

extern uint32_t _estack;                     /* from the linker script: the top of RAM          */
extern uint32_t _sidata, _sdata, _edata;     /* .data: its copy in flash, and its place in RAM  */
extern uint32_t _sbss, _ebss;                /* .bss: variables that start at 0                 */
int main(void);

void Reset_Handler(void)
{
    uint32_t *src = &_sidata, *dst = &_sdata;
    while (dst < &_edata)                    /* 1. copy the initial values of .data into RAM    */
        *dst++ = *src++;
    for (dst = &_sbss; dst < &_ebss; )       /* 2. clear .bss                                   */
        *dst++ = 0;
    main();                                  /* 3. start the program                            */
    for (;;) { }
}

void Default_Handler(void) { for (;;) { } }

/* the vector table: word 0 = the initial stack pointer, word 1 = the reset address, then the handlers */
__attribute__((section(".isr_vector"), used))
const void *vector_table[16] = {
    &_estack,                 /* 0  initial MSP                                         */
    Reset_Handler,            /* 1  reset                                               */
    Default_Handler,          /* 2  NMI                                                 */
    Default_Handler,          /* 3  HardFault                                           */
    Default_Handler,          /* 4  MemManage                                           */
    Default_Handler,          /* 5  BusFault                                            */
    Default_Handler,          /* 6  UsageFault                                          */
    0,                        /* 7  LPC17xx: checksum of words 0..6, added after linking */
    0, 0, 0,                  /* 8 .. 10 reserved                                       */
    Default_Handler,          /* 11 SVCall                                              */
    Default_Handler,          /* 12 debug monitor                                       */
    0,                        /* 13 reserved                                            */
    Default_Handler,          /* 14 PendSV                                              */
    Default_Handler,          /* 15 SysTick                                             */
};
