/*
 * 16x2 LCD (HD44780) in 8-bit mode on the LPC1768 (ARM Cortex-M3)
 * Keil uVision + CMSIS (LPC17xx.h)
 *
 * Wiring (change the #defines if your board uses other pins):
 *   LCD D0..D7 -> P0.15 .. P0.22
 *   LCD RS     -> P0.23        (0 = command, 1 = character)
 *   LCD EN     -> P0.24        (data is latched on the falling edge)
 *   LCD RW     -> GND          (we only write to the LCD)
 *   LCD VSS -> GND, VDD -> +5 V, V0 -> middle of a 10k pot (contrast)
 */
#include <LPC17xx.h>

#define DATA_SHIFT  15
#define DATA_MASK   (0xFFu << DATA_SHIFT)   /* P0.15 .. P0.22 */
#define RS_PIN      (1u << 23)              /* P0.23 */
#define EN_PIN      (1u << 24)              /* P0.24 */

/* ---------- delays: SysTick used as a stopwatch (no interrupt) ---------- */
static void delay_us(uint32_t us)
{
    SysTick->LOAD = us * (SystemCoreClock / 1000000u) - 1u;
    SysTick->VAL  = 0;                       /* restart the count       */
    SysTick->CTRL = 5;                       /* enable, CPU clock       */
    while ((SysTick->CTRL & (1u << 16)) == 0) { }   /* wait: COUNTFLAG */
    SysTick->CTRL = 0;                       /* stop                    */
}

static void delay_ms(uint32_t ms)
{
    while (ms--) {
        delay_us(1000);
    }
}

/* ---------- low level: put one byte on the bus ---------- */
static void lcd_pulse_enable(void)
{
    LPC_GPIO0->FIOSET = EN_PIN;              /* EN high ...             */
    delay_us(1);                             /* ... for at least 450 ns */
    LPC_GPIO0->FIOCLR = EN_PIN;              /* falling edge: LCD reads */
    delay_us(1);
}

static void lcd_write(uint8_t value, uint8_t is_data)
{
    if (is_data) {
        LPC_GPIO0->FIOSET = RS_PIN;          /* RS = 1: a character     */
    } else {
        LPC_GPIO0->FIOCLR = RS_PIN;          /* RS = 0: a command       */
    }
    LPC_GPIO0->FIOCLR = DATA_MASK;                        /* old byte off */
    LPC_GPIO0->FIOSET = (uint32_t)value << DATA_SHIFT;    /* new byte on  */
    lcd_pulse_enable();
    delay_us(50);                            /* most commands take 37 us */
}

static void lcd_cmd(uint8_t cmd)
{
    lcd_write(cmd, 0);
    if (cmd == 0x01 || cmd == 0x02) {
        delay_ms(2);                         /* clear / home take 1.52 ms */
    }
}

static void lcd_data(char c)
{
    lcd_write((uint8_t)c, 1);
}

/* ---------- high level ---------- */
static void lcd_init(void)
{
    LPC_PINCON->PINSEL0 &= ~(3u << 30);      /* P0.15        = GPIO */
    LPC_PINCON->PINSEL1 &= ~0x3FFFFu;        /* P0.16..P0.24 = GPIO */
    LPC_GPIO0->FIODIR   |= DATA_MASK | RS_PIN | EN_PIN;   /* outputs */
    LPC_GPIO0->FIOCLR    = DATA_MASK | RS_PIN | EN_PIN;

    delay_ms(40);                            /* LCD power-up time         */
    lcd_cmd(0x30);  delay_ms(5);             /* wake-up, three times      */
    lcd_cmd(0x30);  delay_us(150);
    lcd_cmd(0x30);
    lcd_cmd(0x38);                           /* 8-bit, 2 lines, 5x8 dots  */
    lcd_cmd(0x0C);                           /* display ON, cursor OFF    */
    lcd_cmd(0x01);                           /* clear the display         */
    lcd_cmd(0x06);                           /* cursor moves to the right */
}

static void lcd_goto(uint8_t row, uint8_t col)
{
    uint8_t addr = (uint8_t)((row ? 0x40 : 0x00) + col);  /* DDRAM address */
    lcd_cmd((uint8_t)(0x80 | addr));                       /* set DDRAM     */
}

static void lcd_print(const char *s)
{
    while (*s) {
        lcd_data(*s++);
    }
}

int main(void)
{
    uint32_t count = 0;
    char num[5];

    SystemCoreClockUpdate();
    lcd_init();
    lcd_goto(0, 0);
    lcd_print("Hello, LPC1768!");
    lcd_goto(1, 0);
    lcd_print("Count: ");

    while (1) {
        num[0] = (char)('0' + (count / 1000) % 10);
        num[1] = (char)('0' + (count / 100) % 10);
        num[2] = (char)('0' + (count / 10) % 10);
        num[3] = (char)('0' + count % 10);
        num[4] = '\0';
        lcd_goto(1, 7);
        lcd_print(num);
        count++;
        delay_ms(1000);
    }
}
