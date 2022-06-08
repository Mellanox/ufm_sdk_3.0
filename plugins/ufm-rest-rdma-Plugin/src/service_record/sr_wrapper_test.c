/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <stdlib.h>

#include "common/defs.h"
#include "service_record/sr_wrapper.h"
#include "common/logger.h"

#define SERVICE_NAME "lalala_service"
#define SERVICE_ID    0x100002c900000002UL
#define SERVICE_ADDRSS "Hello world!"


int main(int argc, char** argv) {
    clx_init_stderr_logger(CLX_LOG_DEBUG);

    bool server = true;

    if (argc == 2) {
        int server_int = atoi(argv[1]);
        server = server_int ? true : false;
        printf("Running app server: %s\n",
               server ? "true" : "false");
    } else {
        printf("Use for server: %s 1\n", argv[0]);
        printf("Use for client: %s 0\n", argv[0]);
        return 1;
    }

    sr_wrapper_ctx_t* context = sr_wrapper_create(SERVICE_NAME, SERVICE_ID, "mlx5_2", 1);

    if (!context) {
        log_error("Unable to allocate sr_wrapper_ctx_t: %s", strerror(errno));
        return 1;
    } else {
        log_info("sr_wrapper_ctx_t init done");
    }

    if (server) {
        const char* address = SERVICE_ADDRSS;
        size_t address_len = strlen(address) + 1;

        log_info("sr_wrapper registering address:%s address_len=%zu", address, address_len);
        if (false == sr_wrapper_register(context, (const void*)address, address_len)) {
            log_error("Unable to register sr_wrapper: %s", strerror(errno));
            return 1;
        } else {
            int sleep_sec = 1000;
            log_info("sr_wrapper register done, sleep %d seconds", sleep_sec);
            sleep(sleep_sec);
        }

        if (false == sr_wrapper_unregister(context)) {
            log_error("Unable to unregister sr_wrapper second time: %s", strerror(errno));
            return 1;
        } else {
            log_info("Unregister done");
        }
    } else {
        char address_buffer[1000];
        size_t address_len = sr_wrapper_query(context, address_buffer, sizeof(address_buffer));
        if (address_len == 0) {
            log_error("Unable to query sr_wrapper: %s", strerror(errno));
            return 1;
        } else {
            log_info("sr_wrapper query done, address_len=%zu address=%.*s", address_len, (int)address_len, address_buffer);
        }
    }

    if (false == sr_wrapper_destroy(context)) {
        log_error("Unable to cleanup service_record: %s", strerror(errno));
        return 1;
    } else {
        log_info("Cleanup done");
    }

    return 0;
}
