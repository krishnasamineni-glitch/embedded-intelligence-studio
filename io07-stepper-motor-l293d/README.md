# io07 · Stepper Motor with L293D Explained

How a microcontroller drives a bipolar stepper motor through an L293D: how a stepper moves in exact steps (1.8 degrees, 200 steps per turn), two coils and the H-bridge, why a driver is needed (current and the inductive spike), the L293D pins, enables and two supplies, wiring with a common ground, the full step sequence 0x5, 0x6, 0xA, 0x9, half stepping with 8 patterns, direction, speed and ramps, the code, the pin patterns seen on an emulated Cortex-M3, holding torque, modern drivers with microstepping, and a practice question.

## Files

* [`stepper_demo.c`](stepper_demo.c) – a bipolar stepper motor through an L293D (LPC1768)
* [`lpc17xx_min.h`](lpc17xx_min.h) – the LPC1768 register addresses this code uses (in Keil you can use the full LPC17xx.h instead)
* [`test_stepper.py`](test_stepper.py) – emulator test: runs the C code with a model of the device and checks the result
* [`run_c.py`](run_c.py) – compiles the C file for the Cortex-M3 and runs it on an emulated LPC1768

The test runs the C file on an emulated Cortex-M3 with the LPC1768 memory map and a model of the device, and checks every register write of the video. It needs the free LLVM tools (`clang`, `ld.lld`, `llvm-objcopy`, `llvm-nm`) and `pip install unicorn`; then, in this folder:

```
python test_stepper.py
```

## Lecture notes

Chapter times (mm:ss) point to the moment in the video.

### Stepper motor + L293D  (00:00)

Today: driving a stepper motor from a microcontroller, through an L293D driver. We will see how a stepper moves in exact steps, why it needs a driver, the step sequences for full steps and half steps, and how to set the direction and the speed. The code runs on an LPC1768, and the pin patterns were checked on an emulated Cortex-M3.

### A motor that moves in steps  (00:25)

A stepper motor does not spin freely like a normal DC motor. It has a permanent magnet rotor with coils around it, and every time we change which coils carry current, the rotor turns by one exact step. A common stepper makes 200 steps per turn, so each step is 1.8 degrees. Count the steps, and you know the position without any sensor.

### A bipolar stepper: two coils  (00:47)

The motor in this video is a bipolar stepper, with two coils, A and B, and four wires. To turn, the current in each coil must flow one way and then the other way. Reversing the current needs an H-bridge for each coil.

### Why a driver?  (01:02)

A port pin can give only a few milliamps, but a coil needs a few hundred. A coil is also an inductor: when its current is switched off, it produces a voltage spike that would destroy a pin. So a driver sits between the microcontroller and the motor. The L293D is a popular choice: it has two H-bridges, up to 600 milliamps per channel, and the built-in clamp diodes that give it the letter D.

### The L293D  (01:29)

The L293D has four inputs, IN1 to IN4, and four outputs that follow them, but with the motor's power. IN1 and IN2 drive coil A, and IN3 and IN4 drive coil B. Two enable pins switch each pair of outputs on, and here we simply tie them high. It has two supplies: 5 volts for its logic, and a separate motor supply, for example 12 volts.

### Wiring  (01:54)

In our circuit, IN1 to IN4 come from P2.0 to P2.3. The L293D inputs see 3.3 volts as a high level, so the LPC1768 can drive them directly. And all the grounds are connected together: the microcontroller, the L293D and the motor supply.

### Full step: two coils on  (02:15)

Now the step sequence. In full step mode, both coils are on all the time, and at each step we reverse one of them: A plus, B plus, then A minus, B plus, then A minus, B minus, then A plus, B minus. With IN1 as bit 0 and IN4 as bit 3, these four patterns are 0x5, 0x6, 0xA and 0x9. After the fourth step, the sequence starts again.

### Half step: 8 patterns  (02:46)

In half step mode, we put a one-coil step between every two-coil step: A plus, then A plus and B plus, then B plus, and so on. That gives 8 patterns per cycle and twice as many steps per turn, 400 instead of 200. The motion is smoother, but the one-coil steps have a little less torque.

### The other direction  (03:07)

To turn the other way, we simply run the same sequence backwards: 0x9, 0xA, 0x6, 0x5. Nothing else changes. In the code, a phase counter goes up for one direction and down for the other.

### Speed: the time between steps  (03:21)

The speed is set by the time between steps. With 200 steps per turn and 5 milliseconds per step, the motor makes 200 steps per second, which is one turn per second, or 60 rpm. If we step too fast, the rotor cannot follow, it misses steps, and the position is lost. So for higher speeds, the step rate is increased slowly: this is called a ramp.

### The code  (03:46)

Here is the code. The table full_step holds the four patterns, and phase remembers where we are. step adds plus or minus 1 to phase, keeps it between 0 and 3 with an AND, and writes the new pattern. coils writes FIOCLR2 for the inputs that must be 0, and then FIOSET2 for the inputs that must be 1, so no other pin of port 2 is touched.

### On the emulator  (04:11)

On the emulator, four forward steps wrote these values. From 0x5, FIOCLR2 got 0x9 and FIOSET2 got 0x6, and the next steps gave 0xA, 0x9 and back to 0x5. Between the two writes, the inputs briefly show 0x4, 0x2, 0x8 and 0x1, which are exactly the half steps in between, so the motor never sees a wrong pattern. Four backward steps gave 0x9, 0xA, 0x6 and 0x5.

| step | FIOCLR2 | FIOSET2 | in between |
|---|---|---|---|
| 0x5 → 0x6 | 0x00000009 | 0x00000006 | 0x4 |
| 0x6 → 0xA | 0x00000005 | 0x0000000A | 0x2 |
| 0xA → 0x9 | 0x00000006 | 0x00000009 | 0x8 |
| 0x9 → 0x5 | 0x0000000A | 0x00000005 | 0x1 |

### Holding torque  (04:42)

When the motor stops with the coils still on, it holds its position firmly: this is the holding torque. But the coils keep drawing current and get warm. If holding is not needed, release switches all inputs off, or the enable pins can be pulled low.

### Modern stepper drivers  (04:58)

The L293D simply connects the coils to the motor supply. Modern stepper drivers, such as the A4988 or the DRV8825, also limit the coil current, and can divide each step into smaller microsteps. They need just two signals from the microcontroller: step and direction.

### Practice  (05:18)

Now try this yourself. Pause the video. A motor has 200 steps per turn. How many full steps turn it by 90 degrees, and how long does that take at 5 milliseconds per step? The answers: 90 degrees is a quarter turn, so 50 steps, and 50 steps times 5 milliseconds is 250 milliseconds.

### Summary  (05:39)

Here is the summary. A stepper turns by one exact step each time the coil pattern changes, here 1.8 degrees. A bipolar stepper needs an H-bridge for each coil, and the L293D gives two, with clamp diodes. The full step sequence is 0x5, 0x6, 0xA, 0x9, backwards for the other direction, and the time between steps sets the speed.

|   | remember |
|---|---|
| stepper | one exact step per coil change (1.8°) |
| bipolar | an H-bridge per coil: L293D has two, + diodes |
| full step | 0x5, 0x6, 0xA, 0x9 |
| direction | the same table backwards |
| speed | the time between steps; ramp up |
