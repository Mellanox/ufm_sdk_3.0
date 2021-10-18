/*
* Copyright (C) Mellanox Technologies Ltd. 2017.  ALL RIGHTS RESERVED.
*
* See file LICENSE for terms.
*/
#include "common/logger.h"

#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <sys/time.h>
#include <syslog.h>
#include <time.h>

typedef enum clx_logging_facility_t {
    CLX_LOGGING_STDERR = 0,
    CLX_LOGGING_SYSLOG,
    CLX_LOGGING_FILE,
} clx_logging_facility_t;

static FILE* log_file = NULL;
static clx_logging_facility_t logging_facility = CLX_LOGGING_STDERR;
clx_log_level_t clx_log_level = CLX_LOG_INFO;

static log_func_t log_func = NULL;

void set_log_func(log_func_t func, int level) {
    log_func = func;
    clx_log_level = (clx_log_level_t)level;
}

log_func_t get_log_func() {
    return log_func;
}

static void dump_timestamp(FILE* fp) {
    char buffer[26];
    int millisec;
    struct tm tm_info;
    struct timespec ts;
    const uint64_t nsecs_in_msec = 1e6;
    const uint64_t msecs_in_sec = 1e3;

    clock_gettime(CLOCK_REALTIME, &ts);

    millisec = ts.tv_nsec/nsecs_in_msec;
    if (millisec >= msecs_in_sec) {
        ts.tv_sec++;
        millisec -= msecs_in_sec;
    }

    localtime_r(&ts.tv_sec, &tm_info);
    strftime(buffer, sizeof(buffer), "[%Y-%m-%d %H:%M:%S", &tm_info);
    fprintf(fp, "%s.%03d] ", buffer, millisec);
}

static const char* priority_level_string(clx_log_level_t level) {
    switch (level) {
        case CLX_LOG_ERROR:
            return "[error] ";
        case CLX_LOG_WARNING:
            return "[warning] ";
        case CLX_LOG_DEBUG:
            return "[debug] ";
        case CLX_LOG_INFO:
            return "[info] ";
        default:
            return "";
    }
}

bool clx_init_stderr_logger(clx_log_level_t level) {
    log_file = stderr;
    logging_facility = CLX_LOGGING_STDERR;
    clx_log_level = level;
    return true;
}

bool clx_init_file_logger(const char* file_mame, clx_log_level_t level) {
    clx_close_logger();
    log_file = fopen(file_mame, "w");
    if (log_file == NULL) {
        clx_init_stderr_logger(level);
        return false;
    }
    logging_facility = CLX_LOGGING_FILE;
    clx_log_level = level;
    return true;
}

bool clx_init_syslog_logger(const char* app_name, clx_log_level_t level) {
    openlog(app_name, LOG_PID|LOG_CONS, LOG_DAEMON);
    logging_facility = CLX_LOGGING_SYSLOG;
    clx_log_level = level;
    return true;
}

void clx_close_logger() {
    switch (logging_facility) {
        case CLX_LOGGING_STDERR:
            break;
        case CLX_LOGGING_SYSLOG:
            closelog();
            break;
        case CLX_LOGGING_FILE:
            fclose(log_file);
            break;
        default:
            break;
    }
    clx_init_stderr_logger(clx_log_level);
}

void _clx_log(clx_log_level_t level, const char* format, ...) {
    va_list args;
    va_start(args, format);
    if (logging_facility == CLX_LOGGING_SYSLOG) {
        vsyslog(level, format, args);
    } else {
        if (log_file == NULL)
            clx_init_stderr_logger(clx_log_level);

        dump_timestamp(log_file);
        fprintf(log_file, "%s", priority_level_string(level));
        vfprintf(log_file, format, args);
        fprintf(log_file, "\n");
        fflush(log_file);
    }
    va_end(args);
}

#define _APPEND(_LINE, _TMP)     do {\
                                       strncat(_LINE, _TMP, sizeof(_TMP) - 1); _LINE[sizeof(_LINE)-1] = '\0'; \
                                 } while (0);
#define _APPEND_STR(_LINE, _TMP) { strcat(_LINE, _TMP);}
#define _OUTPUT(_LINE)          { log_debug("%s", _LINE); memset(_LINE, 0, sizeof(_LINE)); memset(ascii, 0, sizeof(ascii));}

void log_hex(const void* data, size_t size) {
    // do not format the data if it is not going to be output
    if (clx_get_log_level() < CLX_LOG_DEBUG) {
        return;
    }

    char ascii[17];
    size_t i, j;
    ascii[16] = '\0';

    char space[] = " ";
    char space3[] = "   ";
    char tmp[64];
    char line[100];

    memset(line, 0, sizeof(line));

    for (i = 0; i < size; ++i) {
        sprintf(tmp, "%02X ", ((unsigned char*)data)[i]);
        _APPEND(line, tmp);

        if (((unsigned char*)data)[i] >= ' ' && ((unsigned char*)data)[i] <= '~') {
            ascii[i % 16] = ((unsigned char*)data)[i];
        } else {
            ascii[i % 16] = '.';
        }
        if ((i+1) % 8 == 0 || i+1 == size) {
            _APPEND(line, space);
            if ((i+1) % 16 == 0) {
                sprintf(tmp, "|  %s ", ascii);
                _APPEND(line, tmp);
                _OUTPUT(line);
            } else if (i+1 == size) {
                ascii[(i+1) % 16] = '\0';
                if ((i+1) % 16 <= 8) {
                    _APPEND_STR(line, space);
                }
                for (j = (i+1) % 16; j < 16; ++j) {
                    _APPEND_STR(line, space3);
                }
                sprintf(tmp, "|  %s ", ascii);
                _APPEND(line, tmp);
                _OUTPUT(line);
            }
        }
    }
}
