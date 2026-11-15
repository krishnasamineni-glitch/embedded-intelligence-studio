/* pwm_demo.c - the PWM examples of the video: PWM1.1 on P2.0, 1 kHz, 25 % duty (LPC1768, PCLK = 25 MHz) */
#include "lpc17xx_min.h"

void pwm_setup(void)
{
    PINSEL4 = (PINSEL4 & ~3u) | 1u;      /* P2.0: function 01 = PWM1.1              */
    PWM1PR  = 24;                        /* 1 tick = 1 us                            */
    PWM1MR0 = 1000;                      /* period: 1000 us = 1 kHz                  */
    PWM1MR1 = 250;                       /* PWM1.1 high for 250 us: 25 % duty        */
    PWM1MCR = 2;                         /* reset TC on MR0                          */
    PWM1LER = 3;                         /* latch MR0 and MR1                        */
    PWM1PCR = 1u << 9;                   /* PWMENA1: single-edge output PWM1.1 on    */
    PWM1TCR = 9;                         /* counter enable (bit 0) + PWM mode (bit 3) */
}

void pwm_duty(uint32_t high_us)          /* change the duty, glitch free */
{
    PWM1MR1 = high_us;
    PWM1LER = 1u << 1;                   /* takes effect at the next period          */
}

void servo_setup(void)                   /* 50 Hz, 1.5 ms pulse: the middle position */
{
    PWM1PR  = 24;
    PWM1MR0 = 20000;                     /* 20 ms                                    */
    PWM1MR1 = 1500;                      /* 1.5 ms                                   */
    PWM1MCR = 2;
    PWM1LER = 3;
    PWM1PCR = 1u << 9;
    PWM1TCR = 9;
}
