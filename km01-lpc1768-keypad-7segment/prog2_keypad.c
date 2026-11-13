/*
 * Program 2: 3x3 keypad scanning, pressed key shown on the 7-segment display
 * LPC1768 (ARM Cortex-M3), Keil uVision + CMSIS (LPC17xx.h)
 *
 * Wiring (change the #defines if your board uses other pins):
 *   7-segment (common cathode): a..g, dp -> P0.4 .. P0.11 (330 ohm each)
 *   Keypad rows    R1 R2 R3 -> P2.0 P2.1 P2.2
 *   Keypad columns C1 C2 C3 -> P2.3 P2.4 P2.5  (internal pull-ups ON)
 *
 *            C1  C2  C3
 *      R1 [  1   2   3 ]
 *      R2 [  4   5   6 ]
 *      R3 [  7   8   9 ]
 */
#include <LPC17xx.h>

#define SEG_SHIFT  4
#define SEG_MASK   (0xFFu << SEG_SHIFT)     /* P0.4 .. P0.11 */

#define ROW_SHIFT  0
#define ROW_MASK   (0x7u << ROW_SHIFT)      /* P2.0 .. P2.2  */
#define COL_SHIFT  3
#define COL_MASK   (0x7u << COL_SHIFT)      /* P2.3 .. P2.5  */

static const uint8_t seg_code[10] = {
    0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F
};

volatile uint32_t ms_ticks = 0;
void SysTick_Handler(void) { ms_ticks++; }

static void delay_ms(uint32_t ms)
{
    uint32_t start = ms_ticks;
    while ((ms_ticks - start) < ms) { }
}

static void settle(void)                    /* a few microseconds */
{
    volatile uint32_t i;
    for (i = 0; i < 200; i++) { }
}

/* ---------- 7-segment ---------- */
static void seg_init(void)
{
    LPC_PINCON->PINSEL0 &= ~(0xFFFFu << 8);  /* P0.4..P0.11 = GPIO */
    LPC_GPIO0->FIODIR   |= SEG_MASK;
    LPC_GPIO0->FIOCLR    = SEG_MASK;
}

static void seg_show(uint8_t digit)
{
    LPC_GPIO0->FIOCLR = SEG_MASK;
    LPC_GPIO0->FIOSET = (uint32_t)seg_code[digit] << SEG_SHIFT;
}

/* ---------- keypad ---------- */
static void keypad_init(void)
{
    LPC_PINCON->PINSEL4  &= ~0xFFFu;        /* P2.0..P2.5 = GPIO            */
    LPC_PINCON->PINMODE4 &= ~0xFFFu;        /* 00 = internal pull-up ON     */
    LPC_GPIO2->FIODIR    &= ~(ROW_MASK | COL_MASK); /* all inputs (idle)    */
    LPC_GPIO2->FIOCLR     = ROW_MASK;       /* row latch = 0, used when a row is driven */
}

/* Drive one row LOW at a time; a LOW column means the key at (row, col) is pressed.
 * Only the active row is an output, so two pressed keys can never short two outputs.
 * Returns 1..9, or 0 when no key is pressed. */
static uint8_t keypad_scan(void)
{
    uint8_t row, col;
    uint32_t cols;

    for (row = 0; row < 3; row++) {
        LPC_GPIO2->FIODIR &= ~ROW_MASK;                 /* all rows released  */
        LPC_GPIO2->FIODIR |= 1u << (ROW_SHIFT + row);   /* this row drives ... */
        LPC_GPIO2->FIOCLR  = 1u << (ROW_SHIFT + row);   /* ... LOW            */
        settle();
        cols = (LPC_GPIO2->FIOPIN & COL_MASK) >> COL_SHIFT;
        for (col = 0; col < 3; col++) {
            if ((cols & (1u << col)) == 0) {            /* pulled LOW = pressed */
                LPC_GPIO2->FIODIR &= ~ROW_MASK;
                return (uint8_t)(row * 3 + col + 1);
            }
        }
    }
    LPC_GPIO2->FIODIR &= ~ROW_MASK;
    return 0;
}

/* Wait for one key: debounce 20 ms, wait for release, return 1..9 */
static uint8_t keypad_getkey(void)
{
    uint8_t key;
    while (1) {
        key = keypad_scan();
        if (key != 0) {
            delay_ms(20);                               /* contact bounce */
            if (keypad_scan() == key) {
                while (keypad_scan() != 0) { }          /* wait for release */
                delay_ms(20);
                return key;
            }
        }
    }
}

int main(void)
{
    SystemCoreClockUpdate();
    SysTick_Config(SystemCoreClock / 1000);
    seg_init();
    keypad_init();
    seg_show(0);

    while (1) {
        seg_show(keypad_getkey());                      /* show the pressed key */
    }
}
