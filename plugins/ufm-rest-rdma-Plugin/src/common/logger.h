/*
* Copyright (C) Mellanox Technologies Ltd. 2017.  ALL RIGHTS RESERVED.
*
* See file LICENSE for terms.
*/
#ifndef COMMON_LOGGER_H_
#define COMMON_LOGGER_H_

#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include <syslog.h>
#include <stdbool.h>

#include "common/defs.h"
#include "common/timestamp.h"

BEGIN_C_DECLS

typedef enum clx_log_level_t {
    CLX_LOG_OFF       = LOG_EMERG,
    CLX_LOG_ERROR     = LOG_ERR,
    CLX_LOG_WARNING   = LOG_WARNING,
    CLX_LOG_INFO      = LOG_INFO,
    CLX_LOG_DEBUG     = LOG_DEBUG,
} clx_log_level_t;

bool clx_init_stderr_logger(clx_log_level_t level);

bool clx_init_file_logger(const char* file_mame, clx_log_level_t level);

bool clx_init_syslog_logger(const char* app_name, clx_log_level_t level);

void clx_close_logger(void);

void _clx_log(clx_log_level_t level, const char*, ...)
    __attribute__((format(printf, 2, 3)));

static inline clx_log_level_t clx_get_log_level(void) {
    extern clx_log_level_t clx_log_level;
    return clx_log_level;
}

typedef void (*log_func_t)(clx_log_level_t level, const char*);

void set_log_func(log_func_t func, int level);
log_func_t get_log_func(void);

#define clx_log(LOG_LEVEL, ...) \
do { \
    if (clx_get_log_level() >= (LOG_LEVEL)) { \
        log_func_t log_func_ptr = get_log_func(); \
        if (log_func_ptr) { \
            char _tmp_log_string[1000];\
            int _ret = snprintf(_tmp_log_string, sizeof(_tmp_log_string) - 1, __VA_ARGS__); \
            if (_ret >= (int)(sizeof(_tmp_log_string) - 1)) { \
                _tmp_log_string[sizeof(_tmp_log_string) - 1] = '\0'; \
            } \
            log_func_ptr(LOG_LEVEL, _tmp_log_string); \
        } else { \
            _clx_log((LOG_LEVEL), __VA_ARGS__); \
        } \
    } \
} while (0)

#define LOG_IDLE                do { } while (0)

#define log_error(...)      clx_log(CLX_LOG_ERROR, __VA_ARGS__)

#define log_error_throttled(...)    { static clx_timestamp_t last_time = 0; \
                                        if ( (clx_take_timestamp() - last_time) > 10*1000000 ) { \
                                            _clx_log(CLX_LOG_ERROR, __VA_ARGS__); \
                                            last_time = clx_take_timestamp(); } }

#ifndef CLX_LOG_LEVEL
# define CLX_LOG_LEVEL      LOG_DEBUG
#endif

#if CLX_LOG_LEVEL < 1
# define log_warning(...)   LOG_IDLE
#else
# define log_warning(...)   clx_log(CLX_LOG_WARNING, __VA_ARGS__)
#endif

#if CLX_LOG_LEVEL < 3
# define log_info(...)      LOG_IDLE
#else
# define log_info(...)      clx_log(CLX_LOG_INFO, __VA_ARGS__)
#endif

#if CLX_LOG_LEVEL < 5
# define log_debug(...)     LOG_IDLE
#else
# define log_debug(...)     clx_log(CLX_LOG_DEBUG, __VA_ARGS__)
#endif

void log_hex(const void* data, size_t size);  // Only defined for 'debug'

END_C_DECLS

#endif  // COMMON_LOGGER_H_
