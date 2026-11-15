/* keypad_demo.c - the 4x4 keypad of the video (LPC1768):
   rows    R0..R3 on P2.0..P2.3 (the row being scanned is an output driven low, the others are inputs)
   columns C0..C3 on P2.4..P2.7 (inputs with the internal pull-ups: a column reads 1 until a key pulls it low) */
#include "lpc17xx_min.h"

#define ROWS  0x0Fu                      /* P2.0 .. P2.3 */
#define COLS  0xF0u                      /* P2.4 .. P2.7 */

static const char keymap[16] = {
    '1', '2', '3', 'A',                  /* row 0 */
    '4', '5', '6', 'B',                  /* row 1 */
    '7', '8', '9', 'C',                  /* row 2 */
    '*', '0', '#', 'D',                  /* row 3 */
};

void keypad_setup(void)
{
    PINSEL4  &= ~0xFFFFu;                /* P2.0 .. P2.7: function 00 = GPIO          */
    PINMODE4 &= ~0xFFFFu;                /* P2.0 .. P2.7: 00 = pull-up on               */
    FIODIR2  &= ~(ROWS | COLS);          /* all eight pins inputs for now               */
    FIOCLR2   = ROWS;                    /* output latch of the rows = 0                */
}

static void settle(void)                 /* a few microseconds for the column lines to settle */
{
    for (volatile int i = 0; i < 10; i++)
        ;
}

int keypad_scan(void)                    /* key number 0..15 (row * 4 + column), or -1 */
{
    for (int r = 0; r < 4; r++) {
        FIODIR2 = (FIODIR2 & ~ROWS) | (1u << r);     /* only row r is an output: it is low */
        settle();
        uint32_t cols = (FIOPIN2 & COLS) >> 4;        /* a pressed key pulls its column low */
        for (int c = 0; c < 4; c++) {
            if ((cols & (1u << c)) == 0) {
                FIODIR2 &= ~ROWS;                     /* rows back to inputs                */
                return r * 4 + c;
            }
        }
    }
    FIODIR2 &= ~ROWS;
    return -1;
}

char key_char(int k)
{
    return k < 0 ? 0 : keymap[k];
}

/* debouncing: call key_event() every 5 ms (from SysTick or a timer).
   A new key is reported once, after the scan has given the same answer 4 times in a row (20 ms). */
static int last = -1, same = 0, stable = -1;

int key_event(void)
{
    int k = keypad_scan();
    if (k == last) {
        if (same < 4)
            same++;
    } else {
        last = k;                        /* changed: start counting again */
        same = 1;
    }
    if (same == 4 && k != stable) {      /* the same for 4 samples        */
        stable = k;
        if (k >= 0)
            return k;                    /* a press (a release returns -1) */
    }
    return -1;
}
