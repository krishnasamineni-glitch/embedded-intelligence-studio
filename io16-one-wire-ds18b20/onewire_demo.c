/* onewire_demo.c - 1-Wire master by bit-banging a GPIO pin (LPC1768): read a DS18B20 temperature sensor
   DQ on P0.4 with a 4.7 kOhm pull-up to 3.3 V. The pin is never driven high: its output latch stays 0, and
   the program switches it between output (pulls the line low) and input (lets the pull-up raise it). */
#include "lpc17xx_min.h"

#define DQ (1u << 4)                            /* P0.4 */

__attribute__((noinline)) void delay_us(uint32_t us)   /* Timer0 counts microseconds (PR = 24) */
{
    uint32_t start = T0TC;
    while (T0TC - start < us)
        ;
}

static void ow_low(void)     { FIODIR0 |= DQ; }          /* output, latch 0: line low */
static void ow_release(void) { FIODIR0 &= ~DQ; }         /* input: the pull-up takes the line high */
static int  ow_level(void)   { return (FIOPIN0 & DQ) != 0; }

void ow_init(void)
{
    T0PR = 24;  T0TCR = 2;  T0TCR = 1;          /* Timer0: 1 tick = 1 us */
    PINSEL0 &= ~(3u << 8);                      /* P0.4: GPIO           */
    FIOCLR0 = DQ;                               /* output latch = 0     */
    ow_release();
}

int ow_reset(void)                              /* 1 = a device answered */
{
    ow_low();      delay_us(480);               /* reset pulse           */
    ow_release();  delay_us(70);
    int present = !ow_level();                  /* presence pulse: low   */
    delay_us(410);
    return present;
}

void ow_write_bit(int b)
{
    ow_low();
    if (b) { delay_us(6);  ow_release(); delay_us(64); }   /* 1: a short low pulse */
    else   { delay_us(60); ow_release(); delay_us(10); }   /* 0: a long low pulse  */
}

int ow_read_bit(void)
{
    ow_low();  delay_us(6);  ow_release();      /* start the slot                  */
    delay_us(9);
    int b = ow_level();                         /* read at 15 us: the slave holds 0 */
    delay_us(55);
    return b;
}

void ow_write_byte(uint8_t v)                   /* least significant bit first */
{
    for (int i = 0; i < 8; i++) {
        ow_write_bit(v & 1);
        v >>= 1;
    }
}

uint8_t ow_read_byte(void)
{
    uint8_t v = 0;
    for (int i = 0; i < 8; i++)
        v |= (uint8_t)(ow_read_bit() << i);
    return v;
}

uint8_t ow_crc8(const uint8_t *p, int n)        /* Dallas / Maxim CRC-8: x^8 + x^5 + x^4 + 1 */
{
    uint8_t crc = 0;
    while (n--) {
        uint8_t b = *p++;
        for (int i = 0; i < 8; i++) {
            uint8_t mix = (crc ^ b) & 1;
            crc >>= 1;
            if (mix)
                crc ^= 0x8C;
            b >>= 1;
        }
    }
    return crc;
}

int ds18b20_read_temp16(void)                   /* temperature in 1/16 degree, or an error code */
{
    uint8_t s[9];
    if (!ow_reset())
        return -10000;                          /* nobody answered     */
    ow_write_byte(0xCC);                        /* SKIP ROM: one sensor */
    ow_write_byte(0x44);                        /* CONVERT T           */
    while (!ow_read_bit())                      /* 0 = still converting */
        ;
    ow_reset();
    ow_write_byte(0xCC);
    ow_write_byte(0xBE);                        /* READ SCRATCHPAD     */
    for (int i = 0; i < 9; i++)
        s[i] = ow_read_byte();
    if (ow_crc8(s, 8) != s[8])
        return -20000;                          /* damaged data        */
    return (int16_t)(s[0] | (s[1] << 8));
}
