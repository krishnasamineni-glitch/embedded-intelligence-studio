/* i2c_demo.c - I2C master on the LPC1768 (I2C2: SDA2 = P0.10, SCL2 = P0.11, 100 kHz, polling):
   read the temperature register of an LM75-type sensor at address 0x48 */
#include "lpc17xx_min.h"

#define AA   (1u << 2)
#define SI   (1u << 3)
#define STO  (1u << 4)
#define STA  (1u << 5)
#define I2EN (1u << 6)

void i2c_init(void)
{
    PCONP      |= 1u << 26;                          /* PCI2C2: power for I2C2                 */
    PINSEL0     = (PINSEL0 & ~(0xFu << 20)) | (0xAu << 20);   /* P0.10 = SDA2, P0.11 = SCL2   */
    PINMODE0    = (PINMODE0 & ~(0xFu << 20)) | (0xAu << 20);  /* no internal pull resistors    */
    PINMODE_OD0 |= (1u << 10) | (1u << 11);          /* open drain: external pull-ups do the high */
    I2C2SCLH    = 125;                               /* 25 MHz / (125 + 125) = 100 kHz         */
    I2C2SCLL    = 125;
    I2C2CONCLR  = AA | SI | STA | I2EN;              /* clean start                             */
    I2C2CONSET  = I2EN;                              /* enable, master mode                     */
}

static void wait_si(void)
{
    while ((I2C2CONSET & SI) == 0)                   /* SI = 1: the next bus event is done */
        ;
}

int i2c_read_regs(uint8_t addr7, uint8_t reg, uint8_t *buf, int n)   /* 0 = ok, else the bad status */
{
    int st;
    I2C2CONSET = STA;                                /* START                           */
    wait_si();
    if ((st = I2C2STAT) != 0x08) goto stop;
    I2C2DAT = (uint8_t)(addr7 << 1);                 /* address + W                     */
    I2C2CONCLR = STA | SI;
    wait_si();
    if ((st = I2C2STAT) != 0x18) goto stop;          /* 0x18: address sent, ACK back    */
    I2C2DAT = reg;                                   /* register number                 */
    I2C2CONCLR = SI;
    wait_si();
    if ((st = I2C2STAT) != 0x28) goto stop;          /* 0x28: data sent, ACK back       */
    I2C2CONSET = STA;                                /* repeated START                  */
    I2C2CONCLR = SI;
    wait_si();
    if ((st = I2C2STAT) != 0x10) goto stop;
    I2C2DAT = (uint8_t)((addr7 << 1) | 1);           /* address + R                     */
    I2C2CONCLR = STA | SI;
    wait_si();
    if ((st = I2C2STAT) != 0x40) goto stop;          /* 0x40: address sent, ACK back    */
    for (int i = 0; i < n; i++) {
        if (i < n - 1) {
            I2C2CONSET = AA;                         /* answer ACK: more bytes wanted   */
            I2C2CONCLR = SI;
            wait_si();
            if ((st = I2C2STAT) != 0x50) goto stop;
        } else {
            I2C2CONCLR = AA | SI;                    /* answer NACK: the last byte      */
            wait_si();
            if ((st = I2C2STAT) != 0x58) goto stop;
        }
        buf[i] = (uint8_t)I2C2DAT;
    }
    st = 0;
stop:
    I2C2CONSET = STO;                                /* STOP                            */
    I2C2CONCLR = SI;
    return st;
}

int lm75_read_half_degrees(void)                     /* temperature in 0.5 degree steps */
{
    uint8_t b[2];
    if (i2c_read_regs(0x48, 0x00, b, 2) != 0)
        return -9999;
    return (int8_t)b[0] * 2 + (b[1] >> 7);
}
