/*
 * coursework.c
 * Ian Kollipara <ian.kollipara@cune.edu>
 * 2025-01-09
 *
 * Coursework entrypoint file
 */


 // Due to how linux runs sheband (#!) scripts,
 // we cannot use the python entrypoint.
 // Instead, we use this C, which can invoke the script.

 #include <unistd.h>

 int main(int argc, char **argv) {
    setuid(0);
    execv("/usr/local/bin/_coursework", argv);

    return 0;
 }
