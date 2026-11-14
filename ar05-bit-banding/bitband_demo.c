/* bitband_demo.c - blink the LED on P0.22 with bit-banding (one store per change, atomic).
 * LPC1768, Keil uVision + CMSIS. FIO0PIN is at 0x2009C014, inside the SRAM bit-band region:
 * the alias word of bit 22 is 0x233802D8 (see the video). */
#include <LPC17xx.h>
#include "bitband.h"

#define LED  BITBAND(&LPC_GPIO0->FIOPIN, 22)     /* = *(volatile uint32_t *)0x233802D8 */

static void delay(volatile uint32_t n)
{
    while (n--) {
    }
}

int main(void)
{
    LPC_GPIO0->FIODIR |= (1u << 22);              /* P0.22 is an output */
    while (1) {
        LED = 1;                                  /* P0.22 high: one store, no read-modify-write in software */
        delay(2000000);
        LED = 0;                                  /* P0.22 low */
        delay(2000000);
    }
}
