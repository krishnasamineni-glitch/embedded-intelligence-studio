/*
 * Program 1: 7-segment display counter (0 to 9) on LPC1768 (ARM Cortex-M3)
 * Keil uVision + CMSIS (LPC17xx.h)
 *
 * Wiring (change the #defines if your board uses other pins):
 *   7-segment display, COMMON CATHODE (common pin to GND)
 *   a b c d e f g dp  ->  P0.4 P0.5 P0.6 P0.7 P0.8 P0.9 P0.10 P0.11
 *   each segment through a 330 ohm resistor
 */
#include <LPC17xx.h>

#define SEG_SHIFT  4                       /* segment a is on P0.4          */
#define SEG_MASK   (0xFFu << SEG_SHIFT)    /* P0.4 .. P0.11 (a..g, dp)      */

/* bit0 = a, bit1 = b, ... bit6 = g ; 1 = segment ON (common cathode) */
static const uint8_t seg_code[10] = {
    0x3F, 0x06, 0x5B, 0x4F, 0x66,          /* 0 1 2 3 4 */
    0x6D, 0x7D, 0x07, 0x7F, 0x6F           /* 5 6 7 8 9 */
};

volatile uint32_t ms_ticks = 0;

void SysTick_Handler(void)                 /* runs every 1 ms */
{
    ms_ticks++;
}

static void delay_ms(uint32_t ms)
{
    uint32_t start = ms_ticks;
    while ((ms_ticks - start) < ms) { }
}

static void seg_init(void)
{
    LPC_PINCON->PINSEL0 &= ~(0xFFFFu << 8); /* P0.4..P0.11 = GPIO (2 bits per pin) */
    LPC_GPIO0->FIODIR   |= SEG_MASK;        /* P0.4..P0.11 = outputs           */
    LPC_GPIO0->FIOCLR    = SEG_MASK;        /* all segments OFF                */
}

static void seg_show(uint8_t digit)
{
    LPC_GPIO0->FIOCLR = SEG_MASK;                               /* old digit off */
    LPC_GPIO0->FIOSET = (uint32_t)seg_code[digit] << SEG_SHIFT; /* new digit on  */
}

int main(void)
{
    uint8_t d;

    SystemCoreClockUpdate();
    SysTick_Config(SystemCoreClock / 1000); /* 1 ms SysTick interrupt */
    seg_init();

    while (1) {
        for (d = 0; d < 10; d++) {
            seg_show(d);
            delay_ms(1000);
        }
    }
}
