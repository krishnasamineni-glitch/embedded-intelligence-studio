/* sevenseg_demo.c - a 4-digit common-cathode 7-segment display, multiplexed (LPC1768):
   segments a..g, dp on P2.0..P2.7 (bit 0 = a ... bit 6 = g, bit 7 = dp), through a resistor each
   digit enables DIG0..DIG3 on P0.4..P0.7 (each switches one digit's common cathode through a transistor) */
#include "lpc17xx_min.h"

#define SEGS    0xFFu                   /* P2.0 .. P2.7 */
#define DIGITS  0xF0u                   /* P0.4 .. P0.7 */

/* common cathode: 1 = segment on.       gfedcba                                    */
static const uint8_t seg[10] = {
    0x3F, 0x06, 0x5B, 0x4F, 0x66,       /* 0 1 2 3 4 */
    0x6D, 0x7D, 0x07, 0x7F, 0x6F,       /* 5 6 7 8 9 */
};

volatile uint8_t digits[4];             /* the digits to show, DIG0 = left */
static int cur = 0;                     /* the digit that is on now        */

void display_setup(void)
{
    PINSEL4 &= ~0xFFFFu;                /* P2.0 .. P2.7: GPIO   */
    PINSEL0 &= ~0xFF00u;                /* P0.4 .. P0.7: GPIO   */
    FIODIR2 |= SEGS;                    /* outputs              */
    FIODIR0 |= DIGITS;
    FIOCLR0  = DIGITS;                  /* all digits off       */
    SYST_RVR = 200000 - 1;              /* 2 ms at 100 MHz      */
    SYST_CVR = 0;
    SYST_CSR = 7;                       /* CPU clock, interrupt, enable */
}

void display_refresh(void)              /* every 2 ms: the next digit */
{
    FIOCLR0 = DIGITS;                   /* 1. all digits off              */
    FIOCLR2 = SEGS;                     /* 2. the new segment pattern     */
    FIOSET2 = seg[digits[cur]];
    FIOSET0 = 1u << (4 + cur);          /* 3. this digit on               */
    cur = (cur + 1) & 3;                /* next time: the next digit      */
}

void SysTick_Handler(void)
{
    display_refresh();
}

void show_number(unsigned n)            /* 0 .. 9999 */
{
    for (int i = 3; i >= 0; i--) {
        digits[i] = n % 10;
        n /= 10;
    }
}

uint8_t anode_code(uint8_t cathode)     /* common anode: 0 = segment on */
{
    return cathode ^ 0xFF;
}
