# ar08 · ARM Cortex-M3 Exceptions and NVIC Explained

Everything about exceptions on the ARM Cortex-M3: exception numbers, faults, SVCall, PendSV and SysTick, external interrupts (IRQ number + 16), the vector table and VTOR, fixed and programmable priorities, preemption and priority grouping, the NVIC registers, and a complete external interrupt example on the LPC1768 with EINT0 and its handler.

## Files

* [`eint0_led.c`](eint0_led.c) – EINT0 on P2.10 toggles the LED on P0.22: full setup + handler (LPC1768, Keil + CMSIS)

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Exceptions and the NVIC  (00:00)

Today: exceptions and interrupts in the Cortex-M3. We will see the exception types, the vector table, how priorities work, and how to configure the NVIC, with a real example: external interrupt 0 on the LPC1768.

### What is an exception?  (00:17)

An exception is any event that makes the processor stop the normal program, and run a special function called a handler. Interrupts from peripherals, like a timer or a UART, are one kind of exception. Faults, caused by errors in the program, are another kind.

### Exception numbers  (00:34)

Every exception has a number. Numbers 1 to 15 are the system exceptions of the processor. Reset is 1, NMI is 2, and HardFault is 3. Then MemManage, BusFault and UsageFault are 4, 5 and 6. SVCall is 11, PendSV is 14, and SysTick is 15.

### Fault exceptions  (00:55)

The fault exceptions report errors. MemManage means a memory protection violation, BusFault a failed bus transfer, and UsageFault a wrong instruction, like an undefined one. These three are disabled after reset, so by default every fault ends up as a HardFault.

### SVCall, PendSV and SysTick  (01:14)

SVCall runs when the program executes the SVC instruction. This is how a task asks the operating system for a service. PendSV is used by an operating system to switch between tasks. And SysTick is the interrupt of the SysTick timer.

### External interrupts: IRQ + 16  (01:31)

From number 16 upward come the external interrupts, IRQ0, IRQ1 and so on, from the peripherals of the chip. So the exception number is the IRQ number plus 16. The Cortex-M3 supports up to 240 of them. The LPC1768 uses 35, and external interrupt 0, EINT0, is IRQ18, which is exception 34.

### The vector table  (01:57)

The vector table holds the address of every handler, one word per exception. The entry for exception number n is at address n times 4. Entry 0 is special: it holds the initial stack pointer, as we saw at reset.

| address | n | vector: address of the handler |
|---|---|---|
| 0x00 | 0 | initial SP value |
| 0x04 | 1 | Reset_Handler |
| 0x08 | 2 | NMI_Handler |
| 0x0C | 3 | HardFault_Handler |
| ... |  |  |
| 0x3C | 15 | SysTick_Handler |
| 0x40 | 16 | IRQ0: WDT_IRQHandler |
| ... |  |  |
| 0x88 | 34 | EINT0_IRQHandler |

### The vector of EINT0  (02:12)

For EINT0, exception 34, the vector is at 34 times 4, which is 136, or 0x88. When the interrupt comes, the processor reads this word, and jumps to EINT0_IRQHandler. In C, we only need to write a function with exactly this name, and the startup file puts its address into the table.

| address | vector |
|---|---|
| 0x88 | EINT0_IRQHandler |

### Moving the vector table: VTOR  (02:36)

After reset, the vector table is at address 0. But it can be moved, for example to RAM, or behind a boot loader, by writing its new address into the vector table offset register, VTOR.

### Priorities  (02:49)

Every exception has a priority, and a lower number means a higher priority. Reset, NMI and HardFault have fixed negative priorities, minus 3, minus 2 and minus 1, so they are always the most important. All the others are programmable.

| number | exception | priority |
|---|---|---|
| 1 | Reset | −3 |
| 2 | NMI | −2 |
| 3 | HardFault | −1 |
| 4 | MemManage | programmable |
| 5 | BusFault | programmable |
| 6 | UsageFault | programmable |
| 7 – 10 | reserved |  |
| 11 | SVCall | programmable |
| 12 | Debug Monitor | programmable |
| 13 | reserved |  |
| 14 | PendSV | programmable |
| 15 | SysTick | programmable |
| 16 + | IRQ0, IRQ1, ... | programmable |

### Priority bits  (03:06)

Each priority field is 8 bits wide, but chips implement only some of the bits, always the top ones. The LPC1768 implements 5 bits, so it has 32 levels, from 0 to 31. Priority 5, for example, is stored as 5 shifted left by 3, which is 0x28.

### Preemption  (03:25)

Priorities decide what happens when two exceptions meet. If an exception with a higher priority arrives while a handler is running, it interrupts that handler. This is called preemption, or nesting. If its priority is equal or lower, it waits until the current handler ends.

### Priority grouping  (03:42)

The priority can also be split into two parts, with the priority group setting. The upper part, the preemption priority, decides who can interrupt whom. The lower part, the subpriority, only decides the order of interrupts that are waiting.

### The NVIC registers  (03:57)

The NVIC has registers for every interrupt. The set-enable registers at 0xE000E100 enable interrupts, and the clear-enable registers at 0xE000E180 disable them. There are also set-pending and clear-pending registers, active bit registers, and the priority registers at 0xE000E400. Each interrupt has one bit, or one priority byte.

| register | address | function | per IRQ |
|---|---|---|---|
| ISER0 – 7 | 0xE000E100 | set-enable | 1 bit |
| ICER0 – 7 | 0xE000E180 | clear-enable | 1 bit |
| ISPR0 – 7 | 0xE000E200 | set-pending | 1 bit |
| ICPR0 – 7 | 0xE000E280 | clear-pending | 1 bit |
| IABR0 – 7 | 0xE000E300 | active | 1 bit |
| IPR0 – 59 | 0xE000E400 | priority | 1 byte |

### Set-enable  (04:26)

Writing 1 to a bit in a set-enable register enables that interrupt, and writing 0 changes nothing. So we can enable one interrupt without a read-modify-write, and without touching the others. For IRQ18, we write 1 shifted left by 18, which is 0x00040000, to 0xE000E100.

### Example: EINT0 setup  (04:50)

Now the complete example. On the LPC1768, EINT0 is on pin P2.10. First, PINSEL4 selects the EINT0 function for this pin. Then EXTMODE makes it edge sensitive, and EXTPOLAR selects the falling edge. We clear any old flag in EXTINT. Finally, the CMSIS functions set the priority, and enable IRQ18 in the NVIC.

### The interrupt handler  (05:19)

The handler is named EINT0_IRQHandler. Inside, we first clear the flag by writing 1 to EXTINT, otherwise the interrupt would come again immediately. Then we do the work: here, we toggle the LED on P0.22. So every press of the button on P2.10 toggles the LED.

### Practice  (05:40)

Now try this yourself. Pause the video. UART0 is IRQ5 on the LPC1768. What is its exception number, and where is its vector? The answers: exception 21, and the vector is at 21 times 4, which is 84, or 0x54.

### Summary  (06:00)

Here is the summary. Exceptions 1 to 15 belong to the processor, and external interrupts start at 16, so the exception number is the IRQ number plus 16. The vector for exception n is at n times 4. A lower priority number means a higher priority, and the LPC1768 has 32 levels. And to use an interrupt, we configure the peripheral, set the priority, enable it in the NVIC, and clear the flag in the handler.

|   | remember |
|---|---|
| numbers | 1 – 15: processor;  16 +: IRQs  (exception = IRQ + 16) |
| vector table | vector for exception n at n × 4 |
| priority | lower number = higher; LPC1768: 32 levels |
| to use an IRQ | configure the peripheral, set the priority, enable in NVIC |
| handler | clear the flag, then do the work |
