#ifndef __PSTAT_H__
#define __PSTAT_H__

#define NPROC 64

struct pstat {
  int inuse[NPROC];              // whether this slot of the process table is in use (1 or 0)
  int pid[NPROC];                // PID of each process
  int priority[NPROC];           // static priority of each process (0-31, 0 is highest)
  int dynamic_priority[NPROC];   // dynamic priority after aging adjustments
  int state[NPROC];              // process state (UNUSED, SLEEPING, RUNNABLE, RUNNING, ZOMBIE)
  int ticks[NPROC];              // number of ticks each process has accumulated on CPU
  int wait_ticks[NPROC];         // number of ticks each process spent waiting in RUNNABLE
};

#endif // __PSTAT_H__

