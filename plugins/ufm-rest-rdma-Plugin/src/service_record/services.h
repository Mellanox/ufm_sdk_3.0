/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#ifndef SERVICE_RECORD_SERVICES_H_
#define SERVICE_RECORD_SERVICES_H_

#include "service_record/sr.h"

#ifdef __cplusplus
extern "C" {
#endif

#define LOG_LEVEL 0

int services_dev_init(struct sr_dev* dev, const char* dev_name, int port);
int services_dev_update(struct sr_dev* dev);
void services_dev_cleanup(struct sr_dev* dev);

#ifdef __cplusplus
}
#endif

#endif  // SERVICE_RECORD_SERVICES_H_
