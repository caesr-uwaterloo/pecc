

/*************************************************************************/
/*                                                                       */
/*  Copyright (c) 1994 Stanford University                               */
/*                                                                       */
/*  All rights reserved.                                                 */
/*                                                                       */
/*  Permission is given to use, copy, and modify this software for any   */
/*  non-commercial purpose as long as this copyright notice is not       */
/*  removed.  All other uses, including redistribution in whole or in    */
/*  part, are forbidden without prior written permission.                */
/*                                                                       */
/*  This software is provided with absolutely no warranty and no         */
/*  support.                                                             */
/*                                                                       */
/*************************************************************************/

#ifndef _Memory_H
#define _Memory_H 1

#include <pthread.h>
#include "defs.h"
#include "particle.h"
#include "box.h"

#define MAX_LOCKS 2048



#include <pthread.h>
#include <stdlib.h>
#include <semaphore.h>
#include <assert.h>
#if __STDC_VERSION__ >= 201112L
#include <stdatomic.h>
#endif
#include <stdint.h>
#define PAGE_SIZE 4096
#define __MAX_THREADS__ 256

extern pthread_t __tid__[__MAX_THREADS__];
extern unsigned __threads__;
extern pthread_mutex_t __intern__;


typedef struct _G_Mem g_mem;

struct _G_Mem
{
   pthread_mutex_t io_lock;
   pthread_mutex_t mal_lock;
   pthread_mutex_t single_lock;
   pthread_mutex_t count_lock;
   long count;
   pthread_mutex_t (lock_array)[MAX_LOCKS];
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } synch;
   real f_array[MAX_PROCS][NUM_DIM_POW_2];
   real max_x;
   real min_x;
   real max_y;
   real min_y;
   long id;
};
extern g_mem *G_Memory;

typedef struct _Local_Memory local_memory;
struct _Local_Memory {
   long pad_begin[PAD_SIZE];

   box *B_Heap;
   long Index_B_Heap;
   long Max_B_Heap;

   particle **Particles;
   long Num_Particles;
   long Max_Particles;

   box *Childless_Partition;
   box *Parent_Partition[MAX_LEVEL];
   long Max_Parent_Level;

   box *Local_Grid;
   real Local_X_Max;
   real Local_X_Min;
   real Local_Y_Max;
   real Local_Y_Min;

   long Total_Work;
   long Min_Work;
   long Max_Work;

   long Time_Step;
   double Time;
   unsigned long init_done_times;
   time_info Timing[MAX_TIME_STEPS];

   long pad_end[PAD_SIZE];
};
extern local_memory Local[MAX_PROCS];

extern void InitGlobalMemory(void);

#endif /* _Memory_H */
