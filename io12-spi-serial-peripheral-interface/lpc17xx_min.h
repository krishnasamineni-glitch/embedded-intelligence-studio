/* lpc17xx_min.h - the few LPC1768 registers used in these examples, with their real addresses
   (in a Keil project, use LPC17xx.h from CMSIS instead: LPC_PINCON->PINSEL0, LPC_GPIO0->FIODIR, ...) */
#include <stdint.h>
#define REG(a)      (*(volatile uint32_t *)(a))

#define PCONP       REG(0x400FC0C4)     /* power control for peripherals */

#define PINSEL0     REG(0x4002C000)     /* P0.0  .. P0.15 : 2 bits per pin */
#define PINSEL1     REG(0x4002C004)     /* P0.16 .. P0.31 */
#define PINSEL4     REG(0x4002C010)     /* P2.0  .. P2.15 */
#define PINMODE0    REG(0x4002C040)
#define PINMODE1    REG(0x4002C044)
#define PINMODE4    REG(0x4002C050)
#define PINMODE_OD0 REG(0x4002C068)     /* 1 bit per pin: open drain */

#define FIO0DIR     REG(0x2009C000)
#define FIO0MASK    REG(0x2009C010)
#define FIO0PIN     REG(0x2009C014)
#define FIO0SET     REG(0x2009C018)
#define FIO0CLR     REG(0x2009C01C)
#define FIO2DIR     REG(0x2009C040)
#define FIO2PIN     REG(0x2009C054)
#define FIO2SET     REG(0x2009C058)
#define FIO2CLR     REG(0x2009C05C)

/* Timer0 (PCLK = CCLK / 4 = 25 MHz after reset) */
#define T0IR        REG(0x40004000)
#define T0TCR       REG(0x40004004)
#define T0TC        REG(0x40004008)
#define T0PR        REG(0x4000400C)
#define T0MCR       REG(0x40004014)
#define T0MR0       REG(0x40004018)
#define T0CCR       REG(0x40004028)
#define T0CR0       REG(0x4000402C)
#define T0EMR       REG(0x4000403C)

/* NVIC and SysTick (inside the Cortex-M3 core) */
#define NVIC_ISER0  REG(0xE000E100)
#define SYST_CSR    REG(0xE000E010)     /* SysTick CTRL  */
#define SYST_RVR    REG(0xE000E014)     /* SysTick LOAD  */
#define SYST_CVR    REG(0xE000E018)     /* SysTick VAL   */

/* PWM1 */
#define PWM1IR      REG(0x40018000)
#define PWM1TCR     REG(0x40018004)
#define PWM1PR      REG(0x4001800C)
#define PWM1MCR     REG(0x40018014)
#define PWM1MR0     REG(0x40018018)
#define PWM1MR1     REG(0x4001801C)
#define PWM1PCR     REG(0x4001804C)
#define PWM1LER     REG(0x40018050)

/* the same GPIO registers with the names used in the videos (FIODIR0 = FIODIR of port 0, ...) */
#define FIODIR0     FIO0DIR
#define FIOPIN0     FIO0PIN
#define FIOSET0     FIO0SET
#define FIOCLR0     FIO0CLR
#define FIODIR2     FIO2DIR
#define FIOPIN2     FIO2PIN
#define FIOSET2     FIO2SET
#define FIOCLR2     FIO2CLR

/* ADC (PCONP bit 12 must be set first) */
#define AD0CR       REG(0x40034000)     /* control: SEL 7:0, CLKDIV 15:8, BURST 16, PDN 21, START 26:24 */
#define AD0GDR      REG(0x40034004)     /* global data: RESULT 15:4, CHN 26:24, OVERRUN 30, DONE 31 */
#define AD0INTEN    REG(0x4003400C)
#define AD0DR0      REG(0x40034010)     /* channel 0 data */

/* DAC (10 bits, output AOUT on P0.26) */
#define DACR        REG(0x4008C000)     /* VALUE 15:6, BIAS 16 */

/* UART0 (PCLK = 25 MHz after reset). DLL/DLM share addresses with RBR/THR/IER when DLAB = 1. */
#define U0RBR       REG(0x4000C000)     /* read, DLAB = 0: received byte  */
#define U0THR       REG(0x4000C000)     /* write, DLAB = 0: byte to send  */
#define U0DLL       REG(0x4000C000)     /* DLAB = 1: divisor, low byte    */
#define U0DLM       REG(0x4000C004)     /* DLAB = 1: divisor, high byte   */
#define U0FCR       REG(0x4000C008)     /* FIFO control (write)           */
#define U0LCR       REG(0x4000C00C)     /* line control: format, DLAB     */
#define U0LSR       REG(0x4000C014)     /* line status: RDR bit 0, THRE bit 5 */
#define U0FDR       REG(0x4000C028)     /* fractional divider: DIVADDVAL 3:0, MULVAL 7:4 */

/* SPI (the simple SPI block; SCK P0.15, SSEL P0.16, MISO P0.17, MOSI P0.18). PCLK = 25 MHz after reset. */
#define S0SPCR      REG(0x40020000)     /* control: CPHA 3, CPOL 4, MSTR 5, LSBF 6, SPIE 7 */
#define S0SPSR      REG(0x40020004)     /* status: SPIF bit 7 = transfer complete */
#define S0SPDR      REG(0x40020008)     /* data */
#define S0SPCCR     REG(0x4002000C)     /* clock counter: SCK = PCLK / S0SPCCR (even, >= 8) */

/* I2C2 (SDA2 = P0.10, SCL2 = P0.11; PCLK = 25 MHz after reset) */
#define I2C2CONSET  REG(0x400A0000)     /* set: AA bit 2, SI bit 3, STO bit 4, STA bit 5, I2EN bit 6 */
#define I2C2STAT    REG(0x400A0004)     /* status code of the last bus event */
#define I2C2DAT     REG(0x400A0008)     /* data: byte to send / byte received */
#define I2C2SCLH    REG(0x400A0010)     /* SCL high time, in PCLK cycles */
#define I2C2SCLL    REG(0x400A0014)     /* SCL low time */
#define I2C2CONCLR  REG(0x400A0018)     /* clear: AAC bit 2, SIC bit 3, STAC bit 5, I2ENC bit 6 */

/* CAN1 (RD1 = P0.0, TD1 = P0.1; an external CAN transceiver is needed) and the acceptance filter */
#define AFMR        REG(0x4003C000)     /* acceptance filter mode: 2 = bypass, receive all */
#define CAN1MOD     REG(0x40044000)     /* mode: bit 0 RM = reset mode */
#define CAN1CMR     REG(0x40044004)     /* command: TR bit 0, STB1 bit 5 */
#define CAN1SR      REG(0x4004401C)     /* status: TBS1 bit 2 = transmit buffer 1 free */
#define CAN1BTR     REG(0x40044014)     /* bit timing: BRP 9:0, SJW 15:14, TSEG1 19:16, TSEG2 22:20, SAM 23 */
#define CAN1TFI1    REG(0x40044030)     /* TX frame info: DLC 19:16, RTR 30, FF 31 */
#define CAN1TID1    REG(0x40044034)     /* TX identifier */
#define CAN1TDA1    REG(0x40044038)     /* TX data bytes 1..4 */
#define CAN1TDB1    REG(0x4004403C)     /* TX data bytes 5..8 */
