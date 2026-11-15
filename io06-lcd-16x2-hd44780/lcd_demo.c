/* lcd_demo.c - a 16x2 character LCD (HD44780) in 4-bit mode (LPC1768):
   RS on P2.0, E on P2.1, D4..D7 on P2.4..P2.7, RW tied to ground (we only write) */
#include "lpc17xx_min.h"

#define RS    (1u << 0)                 /* P2.0: 0 = command, 1 = character */
#define E     (1u << 1)                 /* P2.1: enable, latched on the falling edge */
#define DATA  0xF0u                     /* P2.4 .. P2.7 = D4 .. D7 */

#ifndef US_LOOPS
#define US_LOOPS 25                     /* loop passes per microsecond at 100 MHz */
#endif

static void delay_us(uint32_t us)
{
    for (volatile uint32_t i = 0; i < us * US_LOOPS; i++)
        ;
}

static void delay_ms(uint32_t ms)
{
    while (ms--)
        delay_us(1000);
}

static void lcd_nibble(uint8_t n)       /* 4 bits on D4..D7, then a pulse on E */
{
    FIOCLR2 = DATA;
    FIOSET2 = (n & 0x0Fu) << 4;
    FIOSET2 = E;
    delay_us(1);                        /* E high for at least 450 ns */
    FIOCLR2 = E;                        /* falling edge: the LCD takes the nibble */
    delay_us(1);
}

static void lcd_byte(uint8_t b, int rs) /* high nibble first, then low nibble */
{
    if (rs)
        FIOSET2 = RS;
    else
        FIOCLR2 = RS;
    lcd_nibble(b >> 4);
    lcd_nibble(b);
    delay_us(50);                       /* most commands take 37 us */
}

void lcd_cmd(uint8_t c)
{
    lcd_byte(c, 0);
    if (c <= 0x03)
        delay_ms(2);                    /* clear and home take 1.52 ms */
}

void lcd_data(char ch)
{
    lcd_byte((uint8_t)ch, 1);
}

void lcd_init(void)
{
    PINSEL4 &= ~0xFF0Fu;                /* P2.0, P2.1, P2.4 .. P2.7: GPIO */
    FIODIR2 |= RS | E | DATA;           /* all six are outputs            */
    FIOCLR2  = RS | E | DATA;
    delay_ms(50);                       /* after power on: more than 40 ms */
    lcd_nibble(0x3);                    /* 8-bit mode, three times: a known state */
    delay_ms(5);
    lcd_nibble(0x3);
    delay_us(150);
    lcd_nibble(0x3);
    delay_us(150);
    lcd_nibble(0x2);                    /* now 4-bit mode */
    delay_us(50);
    lcd_cmd(0x28);                      /* 4-bit, 2 lines, 5x8 dots       */
    lcd_cmd(0x0C);                      /* display on, cursor off         */
    lcd_cmd(0x06);                      /* move right after each character */
    lcd_cmd(0x01);                      /* clear                          */
}

void lcd_goto(int row, int col)         /* line 1 starts at 0x00, line 2 at 0x40 */
{
    lcd_cmd(0x80 | (row ? 0x40 : 0x00) | col);
}

void lcd_print(const char *s)
{
    while (*s)
        lcd_data(*s++);
}

void lcd_char_define(int n, const uint8_t rows[8])   /* custom character n = 0..7 */
{
    lcd_cmd(0x40 | (n << 3));           /* CGRAM address: 8 bytes per character */
    for (int i = 0; i < 8; i++)
        lcd_data((char)rows[i]);
    lcd_cmd(0x80);                      /* back to DDRAM */
}

static const uint8_t heart[8] = { 0x00, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x00, 0x00 };

void demo(void)
{
    lcd_init();
    lcd_goto(0, 0);
    lcd_print("Hello, LPC1768!");
    lcd_goto(1, 0);
    lcd_print("16x2 LCD, 4-bit");
    lcd_char_define(0, heart);
    lcd_goto(1, 15);
    lcd_data(0);                        /* character code 0 = the custom heart */
}
