/* main_add3.c - calls the assembly function add3 from C (Keil uVision, any Cortex-M3 project).
   Add add3.s to the same project, build, and watch x in the debugger: it becomes 42. */
extern int add3(int a, int b, int c);

volatile int x;

int main(void)
{
    x = add3(10, 20, 12);      /* R0 = 10, R1 = 20, R2 = 12 -> R0 = 42 */
    while (1) {
    }
}
