/* adc_demo.c - reading a voltage with the 12-bit ADC of the LPC1768 (channel AD0.0 on P0.23) */
#include "lpc17xx_min.h"

void adc_setup(void)
{
    PCONP    |= 1u << 12;                               /* PCADC: power the ADC first          */
    PINSEL1   = (PINSEL1 & ~(3u << 14)) | (1u << 14);   /* P0.23: function 01 = AD0.0          */
    PINMODE1  = (PINMODE1 & ~(3u << 14)) | (2u << 14);  /* P0.23: 10 = no pull-up, no pull-down */
    AD0CR     = (1u << 0)                               /* SEL: channel 0                      */
              | (1u << 8)                               /* CLKDIV = 1: 25 MHz / 2 = 12.5 MHz   */
              | (1u << 21);                             /* PDN: ADC on                         */
}

uint32_t adc_read(void)                                 /* 0 .. 4095 */
{
    uint32_t g;
    AD0CR |= 1u << 24;                                  /* START = 001: convert now   */
    while (((g = AD0GDR) & (1u << 31)) == 0)            /* wait for DONE              */
        ;
    AD0CR &= ~(7u << 24);                               /* START = 000                */
    return (g >> 4) & 0xFFF;                            /* RESULT: bits 15:4          */
}

uint32_t adc_millivolts(uint32_t n)                     /* VREF = 3.3 V */
{
    return n * 3300u / 4096u;
}

uint32_t adc_read_avg16(void)                           /* average of 16 readings: less noise */
{
    uint32_t sum = 0;
    for (int i = 0; i < 16; i++)
        sum += adc_read();
    return sum / 16;
}
