/* bitband.h - bit-band access for the ARM Cortex-M3.
 * Bit-band regions: SRAM 0x20000000 - 0x200FFFFF (alias 0x22000000) and
 *                   peripherals 0x40000000 - 0x400FFFFF (alias 0x42000000).
 * alias address = alias base + byte offset x 32 + bit number x 4
 * The address may be a byte address with bit 0..7, or a word address with bit 0..31 (same alias word). */
#ifndef BITBAND_H
#define BITBAND_H

#include <stdint.h>

/* the macro from the video (SRAM bit-band region only) */
#define BITBAND_SRAM(addr, bit) \
    (*(volatile uint32_t *)(0x22000000u + (((uint32_t)(addr)) - 0x20000000u) * 32u + (uint32_t)(bit) * 4u))

/* general version: works for both bit-band regions */
#define BITBAND_ALIAS(addr, bit) \
    ((((uint32_t)(addr)) & 0xF0000000u) + 0x02000000u + ((((uint32_t)(addr)) & 0x000FFFFFu) << 5) + ((uint32_t)(bit) << 2))
#define BITBAND(addr, bit)  (*(volatile uint32_t *)BITBAND_ALIAS((addr), (bit)))

#endif
