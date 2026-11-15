/* can_demo.c - CAN1 of the LPC1768 at 500 kbit/s: bit timing and sending one standard frame
   RD1 = P0.0, TD1 = P0.1, to a CAN transceiver (e.g. TJA1050 / MCP2551) on CAN_H, CAN_L */
#include "lpc17xx_min.h"

uint32_t can_btr(uint32_t pclk, uint32_t bitrate, uint32_t tq, uint32_t tseg1, uint32_t tseg2, uint32_t sjw)
{
    uint32_t brp = pclk / (bitrate * tq);       /* time quanta: 25 MHz / (500 k x 10) = 5 */
    return (brp - 1) | ((sjw - 1) << 14) | ((tseg1 - 1) << 16) | ((tseg2 - 1) << 20);
}

void can1_init_500k(void)
{
    PCONP   |= 1u << 13;                        /* PCCAN1                                 */
    PINSEL0  = (PINSEL0 & ~0xFu) | 0x5u;        /* P0.0 = RD1, P0.1 = TD1                  */
    CAN1MOD  = 1;                               /* reset mode: BTR may be changed          */
    CAN1BTR  = can_btr(25000000, 500000, 10, 6, 3, 1);   /* 1 + 6 + 3 = 10 quanta, sample at 70 % */
    CAN1MOD  = 0;                               /* normal mode                            */
    AFMR     = 2;                               /* acceptance filter bypassed: receive all */
}

void can1_send(uint32_t id, const uint8_t *data, uint32_t len)   /* standard 11-bit frame, len <= 8 */
{
    uint32_t a = 0, b = 0;
    for (uint32_t i = 0; i < len && i < 4; i++)
        a |= (uint32_t)data[i] << (8 * i);
    for (uint32_t i = 4; i < len; i++)
        b |= (uint32_t)data[i] << (8 * (i - 4));
    while ((CAN1SR & (1u << 2)) == 0)           /* TBS1: buffer 1 is free                 */
        ;
    CAN1TFI1 = len << 16;                       /* DLC; RTR = 0, FF = 0 (11-bit id)        */
    CAN1TID1 = id & 0x7FF;
    CAN1TDA1 = a;
    CAN1TDB1 = b;
    CAN1CMR  = (1u << 0) | (1u << 5);           /* TR + STB1: send buffer 1               */
}

void send_rpm(uint32_t rpm)                     /* example: id 0x123, 2 bytes, high byte first */
{
    uint8_t d[2] = { (uint8_t)(rpm >> 8), (uint8_t)rpm };
    can1_send(0x123, d, 2);
}
