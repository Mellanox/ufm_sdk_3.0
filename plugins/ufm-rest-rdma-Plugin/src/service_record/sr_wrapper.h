/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#ifndef SERVICE_RECORD_SR_WRAPPER_H_
#define SERVICE_RECORD_SR_WRAPPER_H_


#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

typedef void sr_wrapper_ctx_t;

sr_wrapper_ctx_t* sr_wrapper_create(const char* service_name, uint64_t service_id, const char* dev_name, int port);
bool sr_wrapper_destroy(sr_wrapper_ctx_t* ctx);
bool sr_wrapper_register(sr_wrapper_ctx_t* ctx, const void* addr, size_t addr_size);
bool sr_wrapper_unregister(sr_wrapper_ctx_t* ctx);
size_t sr_wrapper_query(sr_wrapper_ctx_t* ctx, void* addr, size_t addr_size);

#endif  // SERVICE_RECORD_SR_WRAPPER_H_
