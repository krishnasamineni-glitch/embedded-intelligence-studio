/* uart_demo.c - UART0 of the LPC1768: 9600 baud 8N1 on P0.2 (TXD0) and P0.3 (RXD0) */
#include "lpc17xx_min.h"

void uart0_init_9600(void)
{
    PINSEL0 = (PINSEL0 & ~0xF0u) | 0x50u;   /* P0.2 = TXD0, P0.3 = RXD0              */
    U0LCR = 0x83;                           /* 8 bits, no parity, 1 stop, DLAB = 1    */
    U0DLL = 163;                            /* 25 MHz / (16 x 163) = 9586 baud        */
    U0DLM = 0;
    U0LCR = 0x03;                           /* DLAB = 0: THR and RBR again            */
    U0FCR = 0x07;                           /* enable and clear the FIFOs             */
}

void uart0_init_115200(void)                /* with the fractional divider */
{
    PINSEL0 = (PINSEL0 & ~0xF0u) | 0x50u;
    U0LCR = 0x83;
    U0DLL = 9;                              /* 25 MHz / (16 x 9 x 1.5) = 115741 baud  */
    U0DLM = 0;
    U0FDR = (2u << 4) | 1u;                 /* MULVAL = 2, DIVADDVAL = 1: x (1 + 1/2) */
    U0LCR = 0x03;
    U0FCR = 0x07;
}

void uart0_putc(char c)
{
    while ((U0LSR & (1u << 5)) == 0)        /* THRE: wait until the transmitter has room */
        ;
    U0THR = (uint8_t)c;
}

int uart0_getc(void)
{
    while ((U0LSR & 1u) == 0)               /* RDR: wait for a received byte */
        ;
    return (int)(U0RBR & 0xFF);
}

void uart0_puts(const char *s)
{
    while (*s)
        uart0_putc(*s++);
}

void uart0_echo_upper(int n)                /* send back n received characters in capitals */
{
    while (n-- > 0) {
        int c = uart0_getc();
        if (c >= 'a' && c <= 'z')
            c -= 'a' - 'A';
        uart0_putc((char)c);
    }
}

void hello(void)
{
    uart0_init_9600();
    uart0_puts("Hello\r\n");
}
