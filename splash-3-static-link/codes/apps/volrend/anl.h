

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

/*************************************************************************
*                                                                        *
*     anl.H:  ANL macros-related stuff, file should be included at end   *
*              of static definitions section before function definitions *
*                                                                        *
**************************************************************************/

#define PAD 256

struct GlobalMemory {
  long Index;
  //long Counter;
  long Queue[MAX_NUMPROC+1][PAD];
  struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } SlaveBarrier;
  struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } TimeBarrier;
  pthread_mutex_t IndexLock;
  pthread_mutex_t CountLock;
  pthread_mutex_t (QLock)[MAX_NUMPROC+1];
  };


