/* eint0_led.c - external interrupt 0 (EINT0 on pin P2.10) toggles the LED on P0.22.
 * LPC1768, Keil uVision + CMSIS (the startup file puts EINT0_IRQHandler into the vector table, exception 34).
 * A push button from P2.10 to GND gives a falling edge on every press.
 * Note: P2.10 is also the ISP pin - do not hold the button down while resetting the board. */
#include <LPC17xx.h>

void EINT0_IRQHandler(void)
{
    LPC_SC->EXTINT = 1;                    /* clear the EINT0 flag first, or the interrupt comes again at once */
    LPC_GPIO0->FIOPIN ^= (1u << 22);       /* the work: toggle the LED */
}

int main(void)
{
    LPC_GPIO0->FIODIR |= (1u << 22);       /* P0.22: LED output */

    LPC_PINCON->PINSEL4 &= ~(3u << 20);    /* P2.10: clear the function bits 21:20 ... */
    LPC_PINCON->PINSEL4 |=  (1u << 20);    /* ... and select 01 = EINT0 */
    LPC_SC->EXTMODE  |= 1u;                /* EINT0 edge sensitive */
    LPC_SC->EXTPOLAR &= ~1u;               /* falling edge */
    LPC_SC->EXTINT    = 1u;                /* clear any old flag */

    NVIC_SetPriority(EINT0_IRQn, 5);       /* LPC1768: 5 priority bits, stored as 5 << 3 = 0x28 */
    NVIC_EnableIRQ(EINT0_IRQn);            /* IRQ18: writes 1 << 18 to ISER0 (0xE000E100) */

    while (1) {
        /* nothing to do here: the button is handled by the interrupt */
    }
}
