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
#include "service_record/sr.h"
#include "common/logger.h"

#define SERVICE_NAME "lalala_service"
#define SERVICE_ID    0x100002c900000002UL


int main(int argc, char** argv) {
    clx_init_stderr_logger(CLX_LOG_DEBUG);

    struct sr_ctx_t* context;
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

    if (service_record_init(&context, SERVICE_NAME, SERVICE_ID, "mlx5_2", 1, NULL)) {
        log_error("Unable to allocate sharp_sr: %s", strerror(errno));
        return 1;
    } else {
        log_info("Init done");
    }

    if (server) {
        const char* address = "My test data";
        size_t address_len = strlen(address) + 1;
        const uint8_t service_key[SR_128_BIT_SIZE] = {0};

        if (service_record_register_service(context, (const void*)address, address_len,
                                            &service_key, true)) {
            log_error("Unable to register service_record: %s", strerror(errno));
            return 1;
        } else {
            int sleep_sec = 100;
            log_info("Register done, sleep %d seconds", sleep_sec);
            sleep(sleep_sec);
        }

        if (service_record_unregister_service(context, &service_key)) {
            log_error("Unable to unregister service_record second time: %s", strerror(errno));
        } else {
            log_info("Unregister done");
        }
    } else {
        struct sr_dev_service srs[SRS_MAX];
        int num_of_services = service_record_query_service(context, srs, SRS_MAX, -1);
        if (num_of_services <= 0) {
            log_error("Unable to query service_record: %s", strerror(errno));
        } else {
            log_info("Query done");
        }
        service_record_printout_service(srs, num_of_services);
    }

    if (service_record_cleanup(context)) {
        log_error("Unable to cleanup service_record: %s", strerror(errno));
        return 1;
    } else {
        log_info("Cleanup done");
    }

    return 0;
}
