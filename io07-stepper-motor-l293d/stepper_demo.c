/* stepper_demo.c - a bipolar stepper motor through an L293D (LPC1768):
   IN1, IN2 (coil A) and IN3, IN4 (coil B) on P2.0 .. P2.3; EN1,2 and EN3,4 tied high; motor supply on VS */
#include "lpc17xx_min.h"

#define COILS 0x0Fu                     /* P2.0 .. P2.3 = IN1 .. IN4 */

#ifndef US_LOOPS
#define US_LOOPS 25
#endif

/* full step, two coils on:   A+B+  A-B+  A-B-  A+B-     bit 0 = IN1 ... bit 3 = IN4 */
static const uint8_t full_step[4] = { 0x5, 0x6, 0xA, 0x9 };
/* half step: A+  A+B+  B+  A-B+  A-  A-B-  B-  A+B- */
static const uint8_t half_step[8] = { 0x1, 0x5, 0x4, 0x6, 0x2, 0xA, 0x8, 0x9 };

static int phase = 0;

static void delay_ms(uint32_t ms)
{
    for (volatile uint32_t i = 0; i < ms * 1000 * US_LOOPS; i++)
        ;
}

static void coils(uint8_t p)            /* IN1..IN4 = p, without touching other pins */
{
    FIOCLR2 = ~p & COILS;               /* the inputs that must be 0 */
    FIOSET2 = p;                        /* the inputs that must be 1 */
}

void stepper_setup(void)
{
    PINSEL4 &= ~0xFFu;                  /* P2.0 .. P2.3: GPIO   */
    FIODIR2 |= COILS;                   /* outputs              */
    phase = 0;
    coils(full_step[0]);                /* hold the first position */
}

void step(int dir)                      /* one full step: dir = +1 or -1 */
{
    phase = (phase + dir) & 3;
    coils(full_step[phase]);
}

void half_step_to(int k)                /* half-step pattern k = 0..7 */
{
    coils(half_step[k & 7]);
}

void rotate(int steps, int dir, uint32_t ms_per_step)
{
    while (steps-- > 0) {
        step(dir);
        delay_ms(ms_per_step);
    }
}

void release(void)                      /* all coils off: no holding torque, no current */
{
    FIOCLR2 = COILS;
}
