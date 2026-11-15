/* dac_demo.c - the 10-bit DAC of the LPC1768: a fixed voltage and a sine wave on AOUT (P0.26) */
#include "lpc17xx_min.h"

void dac_setup(void)
{
    PINSEL1  = (PINSEL1 & ~(3u << 20)) | (2u << 20);    /* P0.26: function 10 = AOUT           */
    PINMODE1 = (PINMODE1 & ~(3u << 20)) | (2u << 20);   /* P0.26: 10 = no pull-up, no pull-down */
}

void dac_write(uint32_t value)                          /* 0 .. 1023 */
{
    DACR = (value & 0x3FFu) << 6;                       /* VALUE: bits 15:6, BIAS = 0 (fast) */
}

uint32_t dac_value_for_mv(uint32_t mv)                  /* VREF = 3.3 V */
{
    uint32_t v = mv * 1024u / 3300u;
    return v > 1023u ? 1023u : v;                       /* 1024 does not fit in 10 bits */
}

/* one period of a sine, 32 samples: 512 + 511 * sin(2 * pi * k / 32) */
static const uint16_t sine32[32] = {
     512,  612,  708,  796,  873,  937,  984, 1013, 1023, 1013,  984,  937,  873,  796,  708,  612,
     512,  412,  316,  228,  151,   87,   40,   11,    1,   11,   40,   87,  151,  228,  316,  412,
};
static unsigned k = 0;

void dac_next_sample(void)                              /* call from a timer interrupt: 32 x f per second */
{
    DACR = (uint32_t)sine32[k] << 6;
    k = (k + 1) & 31;
}
