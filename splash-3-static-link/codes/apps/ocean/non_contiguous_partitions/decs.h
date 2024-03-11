

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

#define INPROCS      1024
#define MAX_LEVELS     14
#if defined(SPARC_SOLARIS) || defined(__i386__) || defined(__ARM_32BIT_STATE)  //32bit
#define IMAX         2050
#define JMAX         2050
#else //64bit
#define IMAX         8194
#define JMAX         8194
#endif
#define MASTER          0
#define RED_ITER        0
#define BLACK_ITER      1
#define PAGE_SIZE    4096



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


struct global_struct {
   long id;
   long starttime;
   long trackstart;
   double psiai;
   double psibi;
};

struct fields_struct {
   double psi[2][IMAX][JMAX];
   double psim[2][IMAX][JMAX];
};

struct fields2_struct {
   double psium[IMAX][JMAX];
   double psilm[IMAX][JMAX];
};

struct wrk1_struct {
   double psib[IMAX][JMAX];
   double ga[IMAX][JMAX];
   double gb[IMAX][JMAX];
};

struct wrk3_struct {
   double work1[2][IMAX][JMAX];
   double work2[IMAX][JMAX];
};

struct wrk2_struct {
   double work3[IMAX][JMAX];
   double f[IMAX];
};

struct wrk4_struct {
   double work4[2][IMAX][JMAX];
   double work5[2][IMAX][JMAX];
};

struct wrk6_struct {
   double work6[IMAX][JMAX];
};

struct wrk5_struct {
   double work7[2][IMAX][JMAX];
   double temparray[2][IMAX][JMAX];
};

struct frcng_struct {
   double tauz[IMAX][JMAX];
};

struct iter_struct {
   long notdone;
   double work8[IMAX][JMAX];
   double work9[IMAX][JMAX];
};

struct guess_struct {
   double oldga[IMAX][JMAX];
   double oldgb[IMAX][JMAX];
};

struct multi_struct {
   double q_multi[MAX_LEVELS][IMAX][JMAX];
   double rhs_multi[MAX_LEVELS][IMAX][JMAX];
   double err_multi;
   long numspin;
   long spinflag[INPROCS];
};

struct locks_struct {
   pthread_mutex_t idlock;
   pthread_mutex_t psiailock;
   pthread_mutex_t psibilock;
   pthread_mutex_t donelock;
   pthread_mutex_t error_lock;
   pthread_mutex_t bar_lock;
};

struct bars_struct {
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } iteration;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } gsudn;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } p_setup;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } p_redph;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } p_soln;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } p_subph;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_prini;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_psini;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_onetime;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_1;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_2;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_3;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_4;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_5;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_6;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_7;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_8;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_9;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } sl_phase_10;
   struct { pthread_mutex_t bar_mutex; pthread_cond_t bar_cond; unsigned bar_teller; } error_barrier;
};

extern struct global_struct *global;
extern struct fields_struct *fields;
extern struct fields2_struct *fields2;
extern struct wrk1_struct *wrk1;
extern struct wrk3_struct *wrk3;
extern struct wrk2_struct *wrk2;
extern struct wrk4_struct *wrk4;
extern struct wrk6_struct *wrk6;
extern struct wrk5_struct *wrk5;
extern struct frcng_struct *frcng;
extern struct iter_struct *iter;
extern struct guess_struct *guess;
extern struct multi_struct *multi;
extern struct locks_struct *locks;
extern struct bars_struct *bars;

extern double eig2;
extern double ysca;
extern long jmm1;
extern double pi;
extern double t0;

extern long *procmap;
extern long xprocs;
extern long yprocs;

extern long numlev;
extern long imx[MAX_LEVELS];
extern long jmx[MAX_LEVELS];
extern double lev_res[MAX_LEVELS];
extern double lev_tol[MAX_LEVELS];
extern double maxwork;
extern long minlevel;
extern double outday0;
extern double outday1;
extern double outday2;
extern double outday3;

extern long nprocs;

extern double h1;
extern double h3;
extern double h;
extern double lf;
extern double res;
extern double dtau;
extern double f0;
extern double beta;
extern double gpr;
extern long im;
extern long jm;
extern long do_stats;
extern long do_output;
extern long *multi_times;
extern long *total_times;
extern double factjacob;
extern double factlap;

struct Global_Private {
  char pad[PAGE_SIZE];
  double multi_time;
  double total_time;
  long rel_start_x[MAX_LEVELS];
  long rel_start_y[MAX_LEVELS];
  long rel_num_x[MAX_LEVELS];
  long rel_num_y[MAX_LEVELS];
  long eist[MAX_LEVELS];
  long ejst[MAX_LEVELS];
  long oist[MAX_LEVELS];
  long ojst[MAX_LEVELS];
  long eiest[MAX_LEVELS];
  long ejest[MAX_LEVELS];
  long oiest[MAX_LEVELS];
  long ojest[MAX_LEVELS];
  long rlist[MAX_LEVELS];
  long rljst[MAX_LEVELS];
  long rlien[MAX_LEVELS];
  long rljen[MAX_LEVELS];
  long iist[MAX_LEVELS];
  long ijst[MAX_LEVELS];
  long iien[MAX_LEVELS];
  long ijen[MAX_LEVELS];
  long pist[MAX_LEVELS];
  long pjst[MAX_LEVELS];
  long pien[MAX_LEVELS];
  long pjen[MAX_LEVELS];
};

extern struct Global_Private *gp;

extern double i_int_coeff[MAX_LEVELS];
extern double j_int_coeff[MAX_LEVELS];
extern long minlev;

/*
 * jacobcalc.C
 */
void jacobcalc(double x[IMAX][JMAX], double y[IMAX][JMAX], double z[IMAX][JMAX], long pid, long firstrow, long lastrow, long firstcol, long lastcol, long numrows, long numcols);

/*
 * laplacalc.C
 */
void laplacalc(double x[IMAX][JMAX], double z[IMAX][JMAX], long firstrow, long lastrow, long firstcol, long lastcol, long numrows, long numcols);

/*
 * main.C
 */
long log_2(long number);
void printerr(char *s);

/*
 * multi.C
 */
void multig(long my_id);
void relax(long k, double *err, long color, long my_num);
void rescal(long kf, long my_num);
void intadd(long kc, long my_num);
void putz(long k, long my_num);

/*
 * slave1.C
 */
void slave(void);

/*
 * slave2.C
 */
void slave2(long procid, long firstrow, long lastrow, long numrows, long firstcol, long lastcol, long numcols);
