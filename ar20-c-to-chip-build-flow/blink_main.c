/* main.c - blink the LED on P0.22 of the LPC1768, with plain register addresses */
#include <stdint.h>

#define FIODIR0  (*(volatile uint32_t *)0x2009C000)
#define FIOSET0  (*(volatile uint32_t *)0x2009C018)
#define FIOCLR0  (*(volatile uint32_t *)0x2009C01C)
#define LED      (1u << 22)

int blinks = 5;                  /* initialised variable: goes to .data   */
int count;                       /* zero variable:        goes to .bss    */
const char name[] = "LPC1768";   /* constant:             goes to .rodata */

static void delay(volatile uint32_t n) { while (n--) { } }

int main(void)
{
    FIODIR0 |= LED;              /* P0.22 is an output */
    for (count = 0; count < blinks; count++) {
        FIOSET0 = LED;  delay(100000);
        FIOCLR0 = LED;  delay(100000);
    }
    for (;;) { }
}
