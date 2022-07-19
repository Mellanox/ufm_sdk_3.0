/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#include "service_record/sr_wrapper.h"
#include "common/logger.h"
#include "service_record/sr.h"

sr_wrapper_ctx_t* sr_wrapper_create(const char* service_name, uint64_t service_id, const char* dev_name, int port) {
    struct sr_ctx_t* context = NULL;
    if (service_record_init(&context, service_name, service_id, dev_name, port, NULL)) {
        return NULL;
    }
    return context;
}

bool sr_wrapper_destroy(sr_wrapper_ctx_t* ctx) {
    struct sr_ctx_t* sr_ctx = (struct sr_ctx_t*)ctx;
    bool result = true;
    if (service_record_cleanup(sr_ctx)) {
        result = false;
    }
    return result;
}

bool sr_wrapper_register(sr_wrapper_ctx_t* ctx, const void* addr, size_t addr_size) {
    bool result = true;
    struct sr_ctx_t* sr_ctx = (struct sr_ctx_t*)ctx;
    if (service_record_register_service(sr_ctx, (const void*)addr, addr_size, NULL, true)) {
        result = false;
    }
    return result;
}

bool sr_wrapper_unregister(sr_wrapper_ctx_t* ctx) {
    bool result = true;
    struct sr_ctx_t* sr_ctx = (struct sr_ctx_t*)ctx;

    if (service_record_unregister_service(sr_ctx, NULL)) {
        result = false;
    }
    return result;
}

size_t sr_wrapper_query(sr_wrapper_ctx_t* ctx,  void* addr, size_t addr_size) {
    struct sr_dev_service sr;
    struct sr_ctx_t* sr_ctx = (struct sr_ctx_t*)ctx;
    size_t result = 0;

    int num_of_services = service_record_query_service(sr_ctx, &sr, 1, -1);
    if (num_of_services <= 0) {
        return result;
    }

    result = (size_t)sr.data[0];
    result = (addr_size < result) ? addr_size : result;
    memcpy(addr, &sr.data[1], result);
    return result;
}
