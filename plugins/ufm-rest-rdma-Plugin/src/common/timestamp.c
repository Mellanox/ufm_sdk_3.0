/*
* Copyright (C) Mellanox Technologies Ltd. 2018.  ALL RIGHTS RESERVED.
*
* See file LICENSE for terms.
*/
#include "common/timestamp.h"

#include <time.h>
#include <sys/time.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

char* clx_timestamp_to_string(clx_timestamp_t timestamp) {
    time_t seconds = timestamp / 1000000;
    int msec = timestamp % 1000000 / 1000;

    struct tm time;
    struct tm* tmp = localtime_r(&seconds, &time);
    if (tmp == NULL) {
        return NULL;
    }

    const char* format = "%04d-%02d-%02d %02d:%02d:%02d.%03d";
    size_t string_len = snprintf(NULL, 0, format, 1900 + tmp->tm_year,
                                 1 + tmp->tm_mon, tmp->tm_mday, tmp->tm_hour,
                                 tmp->tm_min, tmp->tm_sec, msec);

    char* timestamp_string = (char*) malloc(string_len + 1);
    if (timestamp_string == NULL) {
        return NULL;
    }

    snprintf(timestamp_string, string_len + 1, format,
             1900 + tmp->tm_year, 1 + tmp->tm_mon, tmp->tm_mday,
             tmp->tm_hour, tmp->tm_min, tmp->tm_sec, msec);
    return timestamp_string;
}


long clx_timestamp_diff_seconds(clx_timestamp_t from, clx_timestamp_t to) {
    return (to - from) / 1000000;
}
