/*
 * Application: lift (elevator) floor indicator
 * Press a floor number 1..9 on the keypad; the display moves floor by floor,
 * the decimal point glows while the lift is moving.
 * LPC1768 (ARM Cortex-M3), Keil uVision + CMSIS (LPC17xx.h)
 *
 * Wiring: same as Program 2
 *   7-segment (common cathode): a..g, dp -> P0.4 .. P0.11
 *   Keypad rows P2.0..P2.2, columns P2.3..P2.5 (pull-ups ON)
 */
#include <LPC17xx.h>

#define SEG_SHIFT  4
#define SEG_MASK   (0xFFu << SEG_SHIFT)
#define DP_BIT     (1u << (SEG_SHIFT + 7))   /* dp = P0.11 */
#define ROW_SHIFT  0
#define ROW_MASK   (0x7u << ROW_SHIFT)
#define COL_SHIFT  3
#define COL_MASK   (0x7u << COL_SHIFT)
#define FLOOR_TIME_MS  800                   /* time to travel one floor */

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

static void settle(void)
{
    volatile uint32_t i;
    for (i = 0; i < 200; i++) { }
}

static void seg_init(void)
{
    LPC_PINCON->PINSEL0 &= ~(0xFFFFu << 8);
    LPC_GPIO0->FIODIR   |= SEG_MASK;
    LPC_GPIO0->FIOCLR    = SEG_MASK;
}

static void seg_show(uint8_t digit, uint8_t dp_on)
{
    LPC_GPIO0->FIOCLR = SEG_MASK;
    LPC_GPIO0->FIOSET = ((uint32_t)seg_code[digit] << SEG_SHIFT) | (dp_on ? DP_BIT : 0u);
}

static void keypad_init(void)
{
    LPC_PINCON->PINSEL4  &= ~0xFFFu;
    LPC_PINCON->PINMODE4 &= ~0xFFFu;
    LPC_GPIO2->FIODIR    &= ~(ROW_MASK | COL_MASK);
    LPC_GPIO2->FIOCLR     = ROW_MASK;
}

static uint8_t keypad_scan(void)
{
    uint8_t row, col;
    uint32_t cols;

    for (row = 0; row < 3; row++) {
        LPC_GPIO2->FIODIR &= ~ROW_MASK;
        LPC_GPIO2->FIODIR |= 1u << (ROW_SHIFT + row);
        LPC_GPIO2->FIOCLR  = 1u << (ROW_SHIFT + row);
        settle();
        cols = (LPC_GPIO2->FIOPIN & COL_MASK) >> COL_SHIFT;
        for (col = 0; col < 3; col++) {
            if ((cols & (1u << col)) == 0) {
                LPC_GPIO2->FIODIR &= ~ROW_MASK;
                return (uint8_t)(row * 3 + col + 1);
            }
        }
    }
    LPC_GPIO2->FIODIR &= ~ROW_MASK;
    return 0;
}

static uint8_t keypad_getkey(void)
{
    uint8_t key;
    while (1) {
        key = keypad_scan();
        if (key != 0) {
            delay_ms(20);
            if (keypad_scan() == key) {
                while (keypad_scan() != 0) { }
                delay_ms(20);
                return key;
            }
        }
    }
}

int main(void)
{
    uint8_t current = 1, target;

    SystemCoreClockUpdate();
    SysTick_Config(SystemCoreClock / 1000);
    seg_init();
    keypad_init();
    seg_show(current, 0);                    /* lift waits at floor 1 */

    while (1) {
        target = keypad_getkey();            /* requested floor 1..9 */
        while (current != target) {
            if (target > current) {
                current++;                   /* going up   */
            } else {
                current--;                   /* going down */
            }
            seg_show(current, 1);            /* dp ON = moving */
            delay_ms(FLOOR_TIME_MS);
        }
        seg_show(current, 0);                /* arrived: dp OFF */
    }
}
