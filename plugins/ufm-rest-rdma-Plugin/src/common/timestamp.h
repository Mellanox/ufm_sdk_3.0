/*
* Copyright (C) Mellanox Technologies Ltd. 2018.  ALL RIGHTS RESERVED.
*
* See file LICENSE for terms.
*/
#ifndef COMMON_TIMESTAMP_H_
#define COMMON_TIMESTAMP_H_

#include <sys/time.h>
#include <inttypes.h>
#include <time.h>

#include "common/defs.h"

BEGIN_C_DECLS

typedef uint64_t clx_timestamp_t;


static inline
clx_timestamp_t clx_take_timestamp(void) {
    struct timespec ts;
    uint64_t usec;
    const uint64_t nsecs_in_usec = 1e3;
    const uint64_t usecs_in_sec = 1e6;

    clock_gettime(CLOCK_REALTIME, &ts);

    usec = ts.tv_nsec/nsecs_in_usec;
    if (usec >= usecs_in_sec) {
        ts.tv_sec++;
        usec -= usecs_in_sec;
    }

    return ts.tv_sec * 1000000 + usec;
}

static inline
clx_timestamp_t clx_timestamp_plus_n_sec(clx_timestamp_t timestamp, int sec) {
    return timestamp + sec * 1000000;
}

char* clx_timestamp_to_string(clx_timestamp_t timestamp);

long clx_timestamp_diff_seconds(clx_timestamp_t, clx_timestamp_t);

END_C_DECLS

#endif  // COMMON_TIMESTAMP_H_
