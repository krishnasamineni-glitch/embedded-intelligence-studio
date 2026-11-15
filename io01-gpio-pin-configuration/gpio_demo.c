/* gpio_demo.c - the GPIO examples of the video: an LED on P0.22 that follows a key on P2.10 (LPC1768) */
#include "lpc17xx_min.h"

#define LED  (1u << 22)          /* P0.22 */
#define KEY  (1u << 10)          /* P2.10 */

void gpio_setup(void)
{
    PINSEL1  &= ~(3u << 12);     /* P0.22: function 00 = GPIO   (PINSEL1 bits 13:12) */
    PINSEL4  &= ~(3u << 20);     /* P2.10: function 00 = GPIO   (PINSEL4 bits 21:20) */
    PINMODE4 &= ~(3u << 20);     /* P2.10: 00 = pull-up on (the reset value)         */
    FIO0DIR  |= LED;             /* P0.22 output                                       */
    FIO2DIR  &= ~KEY;            /* P2.10 input                                        */
}

void led_follow_key(void)        /* one pass of the main loop */
{
    if ((FIO2PIN & KEY) == 0)    /* key pressed: the pin is pulled to ground */
        FIO0SET = LED;           /* LED on  */
    else
        FIO0CLR = LED;           /* LED off */
}

void uart0_pins(void)            /* the PINSEL example: P0.2 = TXD0, P0.3 = RXD0 */
{
    PINSEL0 = (PINSEL0 & ~0x000000F0u) | 0x00000050u;
}

int main(void)
{
    gpio_setup();
    for (;;)
        led_follow_key();
}
