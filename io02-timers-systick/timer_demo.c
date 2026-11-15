/* timer_demo.c - the timer examples of the video (LPC1768, CCLK = 100 MHz, PCLK = 25 MHz) */
#include "lpc17xx_min.h"

volatile uint32_t ms;                    /* milliseconds since start */

void timer0_1ms_setup(void)
{
    T0TCR = 2;                           /* hold the counter in reset            */
    T0PR  = 24;                          /* 25 MHz / (24 + 1) = 1 MHz: 1 tick = 1 us */
    T0MR0 = 999;                         /* 0 .. 999 = 1000 ticks = 1 ms          */
    T0MCR = 3;                           /* on MR0: interrupt (bit 0) + reset TC (bit 1) */
    NVIC_ISER0 = 1u << 1;                /* TIMER0 is interrupt number 1          */
    T0TCR = 1;                           /* start                                 */
}

void TIMER0_IRQHandler(void)
{
    T0IR = 1;                            /* clear the MR0 flag (write 1)          */
    ms++;
}

void delay_ms(uint32_t n)
{
    uint32_t start = ms;
    while (ms - start < n) { }
}

void systick_1ms_setup(void)             /* what SysTick_Config(SystemCoreClock / 1000) does */
{
    SYST_RVR = 100000000u / 1000 - 1;    /* 99999 = 0x0001869F                    */
    SYST_CVR = 0;                        /* start from the top                    */
    SYST_CSR = 7;                        /* enable, interrupt, processor clock     */
}

void square_wave_1khz(void)              /* MAT0.0 toggles every 500 us: a 1 kHz square wave */
{
    T0PR  = 24;
    T0MR0 = 499;
    T0MCR = 2;                           /* reset only, no interrupt               */
    T0EMR = 3u << 4;                     /* EMC0 = 11: toggle MAT0.0 on match      */
    T0TCR = 1;
}

uint32_t pulse_us(uint32_t rise, uint32_t fall)   /* two captured TC values, 1 tick = 1 us */
{
    return fall - rise;
}
