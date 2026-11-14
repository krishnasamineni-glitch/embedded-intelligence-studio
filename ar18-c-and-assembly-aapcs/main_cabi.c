/* main_cabi.c - calls the assembly functions of cabi_demo.s from C (Keil uVision, any Cortex-M3 project).
   Add cabi_demo.s to the project, build, and watch the variables in the debugger. */
extern int max2(int a, int b);
extern unsigned long long mul64(unsigned a, unsigned b);
extern int sum5(int a, int b, int c, int d, int e);

volatile int m, s;
volatile unsigned long long p;

int main(void)
{
    m = max2(-5, 3);                 /* a in R0, b in R1, result in R0: 3 */
    p = mul64(0x10000, 0x10000);     /* result in R1:R0: 0x0000000100000000 */
    s = sum5(1, 2, 3, 4, 5);         /* 1..4 in R0..R3, 5 on the stack: 15 */
    while (1) {
    }
}
