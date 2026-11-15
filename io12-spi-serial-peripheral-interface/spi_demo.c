/* spi_demo.c - SPI master on the LPC1768: read the 3-byte ID of a SPI flash memory (command 0x9F)
   SCK P0.15, MISO P0.17, MOSI P0.18, chip select on P0.16 used as a GPIO (active low) */
#include "lpc17xx_min.h"

#define CS (1u << 16)                           /* P0.16 */

void spi_init(void)
{
    PINSEL0 |= 3u << 30;                        /* P0.15 = SCK                           */
    PINSEL1  = (PINSEL1 & ~0x3Fu) | 0x3Cu;      /* P0.16 GPIO, P0.17 = MISO, P0.18 = MOSI */
    FIODIR0 |= CS;                              /* CS: output                             */
    FIOSET0  = CS;                              /* high = no device selected              */
    S0SPCCR  = 8;                               /* SCK = 25 MHz / 8 = 3.125 MHz           */
    S0SPCR   = 1u << 5;                         /* MSTR: master; mode 0, 8 bits, MSB first */
}

uint8_t spi_transfer(uint8_t out)               /* send one byte and receive one byte */
{
    S0SPDR = out;
    while ((S0SPSR & (1u << 7)) == 0)           /* SPIF: transfer complete */
        ;
    return (uint8_t)S0SPDR;
}

uint32_t flash_read_id(void)                    /* manufacturer, type, capacity */
{
    uint32_t id = 0;
    FIOCLR0 = CS;                               /* select the flash   */
    spi_transfer(0x9F);                         /* command: read ID   */
    for (int i = 0; i < 3; i++)
        id = (id << 8) | spi_transfer(0xFF);    /* dummy bytes clock the answer in */
    FIOSET0 = CS;                               /* deselect           */
    return id;
}
