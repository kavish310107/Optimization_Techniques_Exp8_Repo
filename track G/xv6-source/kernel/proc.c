// Per-process CPU scheduling implementation with Priority and Aging for xv6-riscv

#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "riscv.h"
#include "spinlock.h"
#include "proc.h"
#include "defs.h"
#include "pstat.h"

struct cpu cpus[NCPU];
struct proc proc[NPROC];

struct proc *initproc;

int nextpid = 1;
struct spinlock pid_lock;

extern void forkret(void);
static void freeproc(struct proc *p);

extern char trampoline[]; // trampoline.S

// Track G: Priority Scheduler with Aging implementation
// Replaces default Round-Robin in xv6
void
scheduler(void)
{
  struct proc *p;
  struct cpu *c = mycpu();
  
  c->proc = 0;
  for(;;){
    // Avoid deadlock by enabling interrupts on this CPU.
    intr_on();

    struct proc *best_proc = 0;
    int highest_prio = MAX_PRIORITY + 1; // 32 is lower priority than all valid (0-31)

    // Age waiting RUNNABLE processes to prevent starvation
    for(p = proc; p < &proc[NPROC]; p++) {
      acquire(&p->lock);
      if(p->state == RUNNABLE) {
        p->wait_ticks++;
        if(p->wait_ticks >= AGING_THRESHOLD) {
          if(p->dynamic_priority > MIN_PRIORITY) {
            p->dynamic_priority--; // Elevate priority towards 0
          }
          p->wait_ticks = 0;
        }

        // Find the runnable process with the best dynamic priority
        if(p->dynamic_priority < highest_prio) {
          if(best_proc)
            release(&best_proc->lock);
          best_proc = p;
          highest_prio = p->dynamic_priority;
          continue; // keep lock held on candidate
        }
      }
      release(&p->lock);
    }

    if(best_proc != 0) {
      // Dispatched: reset wait ticks and restore dynamic priority back towards base priority
      best_proc->wait_ticks = 0;
      best_proc->state = RUNNING;
      c->proc = best_proc;
      
      swtch(&c->context, &best_proc->context);

      // Process has yielded or timer-interrupted back to scheduler
      c->proc = 0;
      // On return, decay dynamic priority back towards static priority if it was elevated
      if(best_proc->dynamic_priority < best_proc->priority) {
        best_proc->dynamic_priority++;
      }
      release(&best_proc->lock);
    }
  }
}

// Track G: Set static and dynamic priority of a process
int
setpriority(int pid, int new_priority)
{
  if(new_priority < MIN_PRIORITY || new_priority > MAX_PRIORITY)
    return -1;

  struct proc *p;
  for(p = proc; p < &proc[NPROC]; p++){
    acquire(&p->lock);
    if(p->pid == pid && p->state != UNUSED){
      p->priority = new_priority;
      p->dynamic_priority = new_priority;
      p->wait_ticks = 0;
      release(&p->lock);
      return 0;
    }
    release(&p->lock);
  }
  return -1; // PID not found
}

// Track G: Populate process statistics for monitoring and benchmarking
int
getpinfo(struct pstat *st)
{
  if(!st)
    return -1;

  struct proc *p;
  int i = 0;
  for(p = proc; p < &proc[NPROC]; p++, i++){
    acquire(&p->lock);
    st->inuse[i] = (p->state != UNUSED);
    st->pid[i] = p->pid;
    st->priority[i] = p->priority;
    st->dynamic_priority[i] = p->dynamic_priority;
    st->state[i] = p->state;
    st->ticks[i] = p->ticks;
    st->wait_ticks[i] = p->wait_ticks;
    release(&p->lock);
  }
  return 0;
}

