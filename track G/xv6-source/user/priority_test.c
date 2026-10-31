#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pstat.h"
#include "user/user.h"

// CPU intensive calculation to simulate compute workload
void cpu_work(int iterations) {
  volatile double x = 1.0;
  for (int i = 0; i < iterations * 100000; i++) {
    x = x * 1.00001 + 0.00001;
  }
}

int main(int argc, char *argv[]) {
  printf("--- xv6 Priority Scheduler Benchmark ---\n");
  
  int nprocs = 3;
  int pids[3];
  int priorities[3] = {5, 15, 25}; // High, Medium, Low priority

  for (int i = 0; i < nprocs; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("Fork failed!\n");
      exit(1);
    }
    if (pid == 0) {
      // Child process: set priority and execute computational work
      int my_pid = getpid();
      setpriority(my_pid, priorities[i]);
      printf("Child %d started with priority %d\n", my_pid, priorities[i]);
      
      uint start = uptime();
      cpu_work(50);
      uint end = uptime();
      
      printf("Child %d (priority %d) finished in %d ticks\n", my_pid, priorities[i], end - start);
      exit(0);
    } else {
      pids[i] = pid;
    }
  }

  // Parent queries pstat and waits for children
  struct pstat st;
  sleep(5);
  if (getpinfo(&st) == 0) {
    printf("\nProcess Status Snapshot:\n");
    for (int i = 0; i < NPROC; i++) {
      if (st.inuse[i] && (st.pid[i] == pids[0] || st.pid[i] == pids[1] || st.pid[i] == pids[2])) {
        printf("PID %d: static_prio=%d, dyn_prio=%d, ticks=%d, wait_ticks=%d\n",
               st.pid[i], st.priority[i], st.dynamic_priority[i], st.ticks[i], st.wait_ticks[i]);
      }
    }
  }

  for (int i = 0; i < nprocs; i++) {
    wait(0);
  }

  printf("Priority scheduler test completed successfully.\n");
  exit(0);
}

