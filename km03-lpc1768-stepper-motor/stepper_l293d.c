/*
 * Bipolar stepper motor with an L293D on the LPC1768 (ARM Cortex-M3)
 * Full step and half step.  Keil uVision + CMSIS (LPC17xx.h)
 *
 * Wiring (change the #defines if your board uses other pins):
 *   L293D IN1, IN2, IN3, IN4 -> P2.0, P2.1, P2.2, P2.3
 *   L293D EN1 (pin 1), EN2 (pin 9) -> +5 V   (both bridges always enabled)
 *   L293D VCC1 (pin 16) -> +5 V logic, VCC2 (pin 8) -> motor supply (e.g. 12 V)
 *   Coil A -> OUT1 (pin 3), OUT2 (pin 6)    Coil B -> OUT3 (pin 11), OUT4 (pin 14)
 *   L293D GND pins (4, 5, 12, 13) and the board GND connected together
 */
#include <LPC17xx.h>

#define COIL_SHIFT     0
#define COIL_MASK      (0xFu << COIL_SHIFT)   /* P2.0 .. P2.3 */
#define STEPS_PER_REV  200                    /* 1.8 degree motor */

/* bit0 = IN1 (A+), bit1 = IN2 (A-), bit2 = IN3 (B+), bit3 = IN4 (B-) */
static const uint8_t full_step[4] = {        /* two coils ON every step  */
    0x5, 0x6, 0xA, 0x9                       /* A+B+  A-B+  A-B-  A+B-   */
};
static const uint8_t half_step[8] = {        /* one coil, two coils, ... */
    0x1, 0x5, 0x4, 0x6,                      /* A+  A+B+  B+  A-B+       */
    0x2, 0xA, 0x8, 0x9                       /* A-  A-B-  B-  A+B-       */
};

/* ---------- delays: SysTick used as a stopwatch (no interrupt) ---------- */
static void delay_us(uint32_t us)
{
    SysTick->LOAD = us * (SystemCoreClock / 1000000u) - 1u;
    SysTick->VAL  = 0;
    SysTick->CTRL = 5;                       /* enable, CPU clock */
    while ((SysTick->CTRL & (1u << 16)) == 0) { }
    SysTick->CTRL = 0;
}

static void delay_ms(uint32_t ms)
{
    while (ms--) {
        delay_us(1000);
    }
}

/* ---------- motor ---------- */
static void motor_init(void)
{
    LPC_PINCON->PINSEL4 &= ~0xFFu;           /* P2.0..P2.3 = GPIO        */
    LPC_GPIO2->FIODIR   |= COIL_MASK;        /* outputs                  */
    LPC_GPIO2->FIOMASK   = ~COIL_MASK;       /* FIOPIN writes change     */
                                             /* only P2.0..P2.3          */
    LPC_GPIO2->FIOPIN    = 0;                /* all coils off            */
}

static void coils(uint8_t pattern)
{
    LPC_GPIO2->FIOPIN = (uint32_t)pattern << COIL_SHIFT;   /* 4 pins at once */
}

/* dir = 1: one direction, dir = 0: the other (it depends on the wiring) */
static void run_full_step(uint32_t steps, uint8_t dir, uint32_t step_ms)
{
    uint32_t i;
    for (i = 0; i < steps; i++) {
        coils(full_step[dir ? (i % 4) : (3 - i % 4)]);
        delay_ms(step_ms);
    }
}

static void run_half_step(uint32_t steps, uint8_t dir, uint32_t step_ms)
{
    uint32_t i;
    for (i = 0; i < steps; i++) {
        coils(half_step[dir ? (i % 8) : (7 - i % 8)]);
        delay_ms(step_ms);
    }
}

int main(void)
{
    SystemCoreClockUpdate();
    motor_init();

    while (1) {
        run_full_step(STEPS_PER_REV, 1, 10);       /* 1 turn: 200 x 1.8 deg  */
        coils(0);                                  /* coils off: no heating  */
        delay_ms(1000);

        run_half_step(2 * STEPS_PER_REV, 1, 5);    /* 1 more turn: 400 x 0.9 */
        coils(0);
        delay_ms(1000);
    }
}
