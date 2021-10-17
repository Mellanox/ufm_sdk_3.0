/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#ifndef SERVICE_RECORD_SR_H_
#define SERVICE_RECORD_SR_H_

#include <infiniband/umad.h>
#include <infiniband/verbs.h>
#include <linux/types.h>
#include <linux/connector.h>
#include <asm/byteorder.h>
#include <sys/time.h>
#include <stdio.h>
#include <errno.h>

#ifdef __cplusplus
extern "C" {
#endif  // __cplusplus


#define SR_DEV_SERVICE_NAME_MAX          64
#define SR_DEV_SERVICE_DATA_MAX          64
#define SR_DEV_MAX_SERVICES              4
#define SRS_MAX                          64
#define SR_128_BIT_SIZE                  (128/8)

struct sr_dev_service {
    uint64_t id;                            /* Fabric-unique id */
    char     name[SR_DEV_SERVICE_NAME_MAX]; /* Textual name */
    uint8_t  data[SR_DEV_SERVICE_DATA_MAX]; /* Private data */
    uint8_t  port_gid[16];                  /* Port GID */
    uint32_t lease;                         /* Lease time, in sec */
};

struct sr_dev {
    char                  dev_name[UMAD_CA_NAME_LEN];
    int                   port_num;
    union ibv_gid         port_gid;
    uint16_t              port_lid;
    uint16_t              port_smlid;
    int                   portid;
    int                   agent;
    unsigned              seed;
    uint16_t              pkey_index;
    struct sr_dev_service service_cache[SR_DEV_MAX_SERVICES];
    unsigned              fabric_timeout_ms;
    int                   query_sleep;
    uint64_t              sa_mkey;
    uint16_t              pkey;
};

struct sr_ctx_t {
    struct sr_dev* dev;           /* SR device */
    int            sr_lease_time; /* SR lease time */
    int            sr_retries;    /* Number of SR set/get query retries */
    char*          service_name;
};

struct sr_config {
    int      sr_lease_time;
    int      sr_retries;
    int      query_sleep;
    uint64_t sa_mkey;
    uint16_t pkey;          /* pkey for the request */
    unsigned fabric_timeout_ms;
    uint16_t pkey_index;    /* pkey index for MAD */
};

int service_record_init(struct sr_ctx_t** context, const char* service_name,
                        const char* dev_name, int port, struct sr_config* conf);
int service_record_init_via_guid(struct sr_ctx_t** context, const char* service_name, uint64_t guid, struct sr_config* conf);
int service_record_cleanup(struct sr_ctx_t* context);
int service_record_register_service(struct sr_ctx_t* context, const void* addr, size_t addr_size,
                                    const uint8_t (*service_key)[SR_128_BIT_SIZE]);
int service_record_unregister_service(struct sr_ctx_t* context, const uint8_t (*service_key)[SR_128_BIT_SIZE]);
int service_record_query_service(struct sr_ctx_t* context, struct sr_dev_service* srs, int srs_num, int retries);
void service_record_printout_service(struct sr_dev_service* srs, int srs_num);

#ifdef __cplusplus
}
#endif  // __cplusplus

#endif  // SERVICE_RECORD_SR_H_
