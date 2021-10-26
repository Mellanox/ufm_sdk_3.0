/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#include "service_record/sr.h"

#include <stddef.h>
#include <inttypes.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include <infiniband/umad_types.h>
#include <infiniband/umad_sa.h>

#include "service_record/services.h"
#include "common/logger.h"

struct ib_service_record {
    __be64 service_id;         /* 0 */
    __u8 service_gid[16];      /* 1 */
    __be16 service_pkey;       /* 2 */
    __be16 resv;               /* 3 */
    __be32 service_lease;      /* 4 */
    __u8 service_key[16];      /* 5 */
    char service_name[64];     /* 6 */
    struct {
        __u8 service_data8[16];    /* 7 */
        __be16 service_data16[8];  /* 8 */
        __be32 service_data32[4];  /* 9 */
        __be64 service_data64[2];  /* 10 */
    } service_data;
};

#define BIT(x) (1UL << (x))
#define SR_DEV_SERVICE_REGISTER_RETRIES  20
#define SR_QUERY_SLEEP                   500000
#define SR_LEASE_TIME                    2000
#define SR_RETRIES                       20
#define SR_DEV_PKEY                      0xffff
#define SA_MKEY                          1
#define SA_FABRIC_TIMEOUT                200
#define SA_WELL_KNOWN_GUID               0x0200000000000002


typedef typeof(((struct umad_port*)0)->port_guid) umad_guid_t;

static int dev_sa_response_method(int method) {
    switch (method) {
    case UMAD_METHOD_GET:
    case UMAD_SA_METHOD_GET_TABLE:
    case UMAD_METHOD_REPORT:
    case UMAD_METHOD_TRAP:
    case UMAD_SA_METHOD_GET_TRACE_TABLE:
    case UMAD_SA_METHOD_GET_MULTI:
    case UMAD_SA_METHOD_DELETE:
        return method;
    case UMAD_METHOD_SET:
        return UMAD_METHOD_GET;
    default:
        return -EINVAL;
    }
}

static inline int report_sa_err(struct sr_dev* dev, uint16_t mad_status) {
    static const char* mad_invalid_field_errors[] = {
        [1] = "Bad version or class",
        [2] = "Method not supported",
        [3] = "Method/attribute combination not supported",
        [4] = "Reserved",
        [5] = "Reserved",
        [6] = "Reserved",
        [7] = "Invalid value in one or more fields of attribute or attribute modifier"
    };

    static const char* sa_errors[] = {
        [1] = "ERR_NO_RESOURCES",
        [2] = "ERR_REQ_INVALID",
        [3] = "ERR_NO_RECORDS",
        [4] = "ERR_TOO_MANY_RECORDS",
        [5] = "ERR_REQ_INVALID_GID",
        [6] = "ERR_REQ_INSUFFICIENT_COMPONENTS",
        [7] = "ERR_REQ_DENIED",
    };

    log_error("OpenSM request failed with status 0x%04x", mad_status);

    uint8_t status = (mad_status >> 2) & 0x7;
    if (status) {
        log_error("MAD status: %s", mad_invalid_field_errors[status]);
    }
    uint8_t sa_status = mad_status >> 8;
    if (sa_status > 0 && sa_status <= 7) {
        log_error("SA status field: %s", sa_errors[sa_status]);
    }

    return EPROTO;
}

static int dev_sa_query(struct sr_dev* dev, int method, int attr,
                        uint64_t comp_mask, void* req_data, int req_size,
                        void** resp_data, int* resp_attr_size) {
    struct ib_user_mad* umad;
    struct umad_sa_packet* sa_mad;
    void* newumad;
    int record_size, num_records;
    uint16_t mad_status;
    size_t data_size;
    int response_method, match, len, ret;
    __be64 sa_mkey;
    uint64_t tid;
    union ibv_gid sa_gid;

    if (req_size > UMAD_LEN_SA_DATA) {
        return -ENOBUFS;
    }

    /* check SA method */
    if ((ret = dev_sa_response_method(method)) < 0) {
        log_error("Unsupported SA method %d", method);
        goto out;
    }
    response_method = ret;

    len = sizeof(*umad) + sizeof(*sa_mad);
    umad = (struct ib_user_mad*) calloc(1, len);
    if (!umad) {
        log_error("Cannot allocate memory for umad: %m");
        ret = -ENOMEM;
        goto out;
    }

    tid = rand_r(&dev->seed);

    umad->addr.qpn = __cpu_to_be32(1);
    umad->addr.qkey = __cpu_to_be32(UMAD_QKEY);
    umad->addr.pkey_index = dev->pkey_index;
    umad->addr.lid = __cpu_to_be16(dev->port_smlid);
    umad->addr.sl = 0;        /* !!! */
    umad->addr.path_bits = 0;    /* !!! */

    sa_gid.global.subnet_prefix = dev->port_gid.global.subnet_prefix;
    sa_gid.global.interface_id = __cpu_to_be64(SA_WELL_KNOWN_GUID);

    umad->addr.grh_present = 1;
    memcpy(&umad->addr.gid, sa_gid.raw, sizeof(umad->addr.gid));

    sa_mad = (struct umad_sa_packet*) umad->data;
    sa_mad->mad_hdr.base_version = 1;
    sa_mad->mad_hdr.mgmt_class = UMAD_CLASS_SUBN_ADM;
    sa_mad->mad_hdr.class_version = UMAD_SA_CLASS_VERSION;
    sa_mad->mad_hdr.method = method;
    sa_mad->mad_hdr.tid = __cpu_to_be64(tid);
    sa_mad->mad_hdr.attr_id = __cpu_to_be16(attr);
    sa_mkey = __cpu_to_be64(dev->sa_mkey);
    memcpy(sa_mad->sm_key, &sa_mkey, sizeof(sa_mad->sm_key));
    sa_mad->comp_mask = __cpu_to_be64(comp_mask);
    if (req_data) {
        memcpy(sa_mad->data, req_data, req_size);
    }

    if ((ret = umad_send(dev->portid, dev->agent, umad, sizeof(*sa_mad),
                         dev->fabric_timeout_ms, 0)) < 0) {
        log_error("umad_send failed: %s. attr 0x%x method 0x%x",
                  strerror(errno), attr, method);
        goto out_free_umad;
    }

    /* Receive response */
    do {
        uint64_t mad_tid;

        /* Receive one MAD */
        len = sizeof(*sa_mad);
        do {
            if (!(newumad = realloc(umad, sizeof(*umad) + len))) {
                log_error("Unable to realloc umad");
                goto out_free_umad;
            } else {
                umad = newumad;
            }
            ret = umad_recv(dev->portid, umad, &len,
                            dev->fabric_timeout_ms);
        } while (ret < 0 && errno == ENOSPC);

        if (ret < 0) {
            log_info("umad_recv returned %d (%s). attr 0x%x method 0x%x",
                     ret, strerror(errno), attr, method);
            goto out_free_umad;
        }

        if ((ret = umad_status(umad)) < 0) {
            ret = -EPROTO;
            log_error("umad_status failed: %d", ret);
            goto out_free_umad;
        }

        match = 1;
        sa_mad = (struct umad_sa_packet*) umad->data;
        /* Check SubnAdm class */
        if (sa_mad->mad_hdr.mgmt_class != UMAD_CLASS_SUBN_ADM) {
            log_warning("Mismatched MAD class: got %d, expected %d",
                        sa_mad->mad_hdr.mgmt_class,
                        UMAD_CLASS_SUBN_ADM);
            match = 0;
        }

        /* Check MAD method */
        if ((sa_mad->mad_hdr.method & ~UMAD_METHOD_RESP_MASK) !=
                response_method) {
            log_info("Mismatched SA method: got 0x%x, expected 0x%x",
                     sa_mad->mad_hdr.method & ~UMAD_METHOD_RESP_MASK,
                     response_method);
            match = 0;
        }
        if (!(sa_mad->mad_hdr.method & UMAD_METHOD_RESP_MASK)) {
            log_info("Not a Response MAD");
            match = 0;
        }

        /* Check MAD transaction ID. Cut it to 32 bits. */
        mad_tid = (uint32_t) __be64_to_cpu(sa_mad->mad_hdr.tid);
        if (mad_tid != tid) {
            log_info("Mismatched TID: got 0x%" PRIx64 ", expected 0x%" PRIx64, mad_tid, tid);
            match = 0;
        }
    } while (!match);

    /* Check MAD status */
    if ((mad_status = __be16_to_cpu(sa_mad->mad_hdr.status))) {
        report_sa_err(dev, mad_status);
        goto out_free_umad;
    }

    /* Check MAD length */
    if (len < offsetof(struct umad_sa_packet, data)) {
        log_error("MAD too short: %d bytes", len);
        ret = -EPROTO;
        goto out_free_umad;
    }
    data_size = len - offsetof(struct umad_sa_packet, data);

    /* Calculate record size */
    record_size = __be16_to_cpu(sa_mad->attr_offset) * 8;
    if (method == UMAD_SA_METHOD_GET_TABLE) {
        num_records = record_size ? (data_size / record_size) : 0;
    } else {
        num_records = 1;
    }

    /* Copy data to a new buffer */
    if (resp_data) {
        if (!(*resp_data = malloc(data_size))) {
            ret = -ENOMEM;
            goto out_free_umad;
        }
        memcpy(*resp_data, sa_mad->data, data_size);
    }

    if (resp_attr_size) {
        *resp_attr_size = record_size;
    }

    ret = num_records;

out_free_umad:
    free(umad);    /* release UMAD */
out:
    return ret;
}

static int dev_sa_query_retries(struct sr_dev* dev, int method, int attr,
                                uint64_t comp_mask, void* req_data,
                                int req_size, void** resp_data,
                                int* resp_attr_size, int allow_zero,
                                int retries) {
    int retries_orig = retries;
    int ret, dev_updated = 0;
    uint16_t prev_lid;

retry:
    for (;;) {
        ret = dev_sa_query(dev, method, attr, comp_mask, req_data,
                           req_size, resp_data, resp_attr_size);
        retries--;
        if (ret > 0 || (allow_zero && ret == 0) || retries <= 0) {
            log_info("Found %d service records", ret);
            break;
        }

        if (ret == 0) {
            log_info("sa_query() returned empty set, %d retries left", retries);
            free(*resp_data);
            *resp_data = NULL;
        } else if (retries == 0) {
            log_error("Unable to query SR: %s, %d retries left", strerror(ret), retries);
        }

        usleep(dev->query_sleep);
    }

    prev_lid = dev->port_lid;
    if (ret < 0 && !dev_updated && method == UMAD_SA_METHOD_GET_TABLE && !services_dev_update(dev)) {
        log_info("%s:%d device updated", dev->dev_name, dev->port_num);
        if (dev->port_lid != prev_lid) {
            log_warning("%s:%d LID change", dev->dev_name, dev->port_num);
        }

        retries = retries_orig;
        dev_updated = 1;
        goto retry;
    }

    if (ret < 0) {
        log_error("Failed to query SR: %s", strerror(-ret));
    }

    return ret;
}

static void save_service(struct sr_dev* dev, struct sr_dev_service* service) {
    for (int i = 0; i < SR_DEV_MAX_SERVICES; ++i)
        if (dev->service_cache[i].id == service->id ||
                dev->service_cache[i].id == 0) {
            dev->service_cache[i] = *service;
            log_info("Service 0x%016" PRIx64 " saved in cache %d", service->id, i);

            return;
        }

    log_warning("No room to save service record '%s' id 0x%016" PRIx64,
                service->name, service->id);
}

static void remove_service(struct sr_dev* dev, uint64_t id) {
    int i, j;

    for (i = 0; i < SR_DEV_MAX_SERVICES && dev->service_cache[i].id == id; ++i) {}

    if (i >= SR_DEV_MAX_SERVICES) {
        log_error("No service id 0x%016" PRIx64 " to remove from the cache", id);
        return;
    }

    /* Replace index i with last service entry */
    for (j = i; j < SR_DEV_MAX_SERVICES && dev->service_cache[j].id != 0; ++j) {}
    if (j < SR_DEV_MAX_SERVICES) {
        dev->service_cache[i] = dev->service_cache[j];
        dev->service_cache[j].id = 0;
    }
    log_info("Service 0x%016" PRIx64 " removed from cache %d", id, i);
}

static int dev_register_service(struct sr_dev* dev,
                                struct sr_dev_service* service,
                                const uint8_t (*service_key)[SR_128_BIT_SIZE]) {
    struct ib_service_record record;
    uint64_t comp_mask = BIT(0) | BIT(1) | BIT(2) | BIT(4) | BIT(6) | \
                         BIT(7) | BIT(8) | BIT(9) | BIT(10) | BIT(11) | \
                         BIT(12) | BIT(13) | BIT(14) | BIT(15) | BIT(16) | \
                         BIT(17) | BIT(18) | BIT(19) | BIT(19) | BIT(20) | \
                         BIT(21) | BIT(22) | BIT(23) | BIT(24) | BIT(25) | \
                         BIT(26) | BIT(27) | BIT(28) | BIT(29) | BIT(30) | \
                         BIT(31) | BIT(32) | BIT(33) | BIT(34) | BIT(35) | \
                         BIT(36); /* ServiceID, ServiceGID, ServicePKey, ServiceLease, ServiceName, and all ServiceData fields */
    int ret;

    memset(&record, 0, sizeof(record));
    record.service_id    = __cpu_to_be64(service->id);
    record.service_pkey  = __cpu_to_be16(dev->pkey);
    record.service_lease = __cpu_to_be32(service->lease);
    strncpy(record.service_name, service->name, sizeof(record.service_name));
    memcpy(&record.service_data, service->data, sizeof(service->data));
    memcpy(&record.service_gid, &dev->port_gid, sizeof(record.service_gid));

    if (service_key) {
        memcpy(&record.service_key, service_key, sizeof(record.service_key));
        comp_mask |= BIT(5);
    }

    ret = dev_sa_query_retries(dev, UMAD_METHOD_SET, UMAD_SA_ATTR_SERVICE_REC,
                               comp_mask, &record, sizeof(record),
                               NULL, NULL, 1,
                               SR_DEV_SERVICE_REGISTER_RETRIES);
    if (ret < 0) {
        return ret;
    }

    save_service(dev, service);
    log_info("Service `%s' id 0x%016" PRIx64 " is registered",
             service->name, service->id);

    return 0;
}

static int dev_unregister_service(struct sr_dev* dev, uint64_t id,
                                  uint8_t* port_gid,
                                  const uint8_t (*service_key)[SR_128_BIT_SIZE]) {
    struct ib_service_record record;
    uint64_t comp_mask = BIT(0) | BIT(1) | BIT(2);
    int ret;

    remove_service(dev, id);

    memset(&record, 0, sizeof(record));
    record.service_id   = __cpu_to_be64(id);
    record.service_pkey = __cpu_to_be16(dev->pkey);
    if (port_gid) {
        memcpy(&record.service_gid, port_gid, sizeof(record.service_gid));
    } else {
        memcpy(&record.service_gid, &dev->port_gid, sizeof(record.service_gid));
    }

    if (service_key) {
        memcpy(&record.service_key, service_key, sizeof(record.service_key));
        comp_mask |= BIT(5);
    }

    if ((ret = dev_sa_query_retries(dev, UMAD_SA_METHOD_DELETE, UMAD_SA_ATTR_SERVICE_REC,
                                    comp_mask, &record, sizeof(record),
                                    NULL, NULL, 1,
                                    SR_DEV_SERVICE_REGISTER_RETRIES)) < 0) {
        return ret;
    }

    log_info("Service 0x%016" PRIx64 " unregistered", id);

    return 0;
}

static int dev_get_service(struct sr_ctx_t* context, const char* name,
                           struct sr_dev_service* services,
                           int max, int retries, int just_copy) {
    struct ib_service_record* response;
    void* raw_data = NULL;
    int record_size = 0;
    int i, j;

    int ret = dev_sa_query_retries(context->dev, UMAD_SA_METHOD_GET_TABLE,
                                   UMAD_SA_ATTR_SERVICE_REC, 0, NULL, 0,
                                   &raw_data, &record_size, 0, retries);
    if (ret < 0) {
        return ret;
    }

    for (i = 0, j = 0; i < ret && j < max; ++i) {
        response = (struct ib_service_record*)((char*)raw_data + i * record_size);

        if (just_copy ||
                (strlen(response->service_name) == strlen(name) &&
                 !strcmp(response->service_name, name))) {
            services[j].id    = __be64_to_cpu(response->service_id);
            services[j].lease = context->sr_lease_time;
            strncpy(services[j].name, response->service_name,
                    sizeof(services[j].name));
            memcpy(services[j].data,  &response->service_data,
                   sizeof(services[j].data));
            memcpy(services[j].port_gid, response->service_gid,
                   sizeof(services[j].port_gid));

            log_info("Found SR: %d) %s 0x%016" PRIx64,
                     j, services[j].name, services[j].id);

            j++;
        }
    }
    free(raw_data);

    return j;
}

static int guid2dev(uint64_t guid, char* dev_name, int* port) {
    char ca_names_array[UMAD_MAX_DEVICES][UMAD_CA_NAME_LEN];
    char dev_name_buf[UMAD_CA_NAME_LEN];
    umad_guid_t pguids_array[UMAD_CA_MAX_PORTS + 1];
    int ca_num = 0, pguid_num = 0;
    int ca_idx, port_num_idx;
    umad_ca_t umad_ca;

    if (!dev_name || !port) {
        log_error("device name or port number parameters were not specified");
        return -1;
    }

    /* if guid is zero, find the first active port */
    if (!guid) {
        strcpy(dev_name, "");
        *port = 0;
        goto found;
    }

    /* get all local cas */
    if ((ca_num = umad_get_cas_names(ca_names_array, UMAD_MAX_DEVICES)) < 0) {
        log_error("unable to umad_get_cas_names");
        return 1;
    }

    /* check for requested guid */
    for (ca_idx = 0; ca_idx < ca_num; ca_idx++) {
        pguid_num = umad_get_ca_portguids(ca_names_array[ca_idx],
                                          pguids_array,
                                          UMAD_CA_MAX_PORTS + 1);
        if (pguid_num < 0) {
            log_error("unable to umad_get_ca_portguids");
            return 1;
        }

        for (port_num_idx = 0; port_num_idx < UMAD_CA_MAX_PORTS + 1 &&
                port_num_idx < pguid_num; port_num_idx++) {
            if (guid == pguids_array[port_num_idx]) {
                strcpy(dev_name, ca_names_array[ca_idx]);
                *port = port_num_idx;
                goto found;
            }
        }
    }

    log_error("unable to find requested guid 0x%" PRIx64"", guid);

    return 1;

found:
    /* validate that node is an IB node type */
    if (strcmp(dev_name, "") == 0) {
        if (umad_get_ca(NULL, &umad_ca) < 0) {
            log_error("unable to umad_get_ca");
            return 1;
        }
    } else {
        strncpy(dev_name_buf, dev_name, sizeof(dev_name_buf) -1);
        dev_name_buf[sizeof(dev_name_buf) -1] = '\0';

        if (umad_get_ca(dev_name_buf, &umad_ca) < 0) {
            log_error("unable to umad_get_ca");
            return 1;
        }
    }

    if (umad_ca.node_type < 1 || umad_ca.node_type > 3) {
        log_error("Type %d of node \'%s\' is not an IB node type",
                  umad_ca.node_type, umad_ca.ca_name);
        umad_release_ca(&umad_ca);
        return 1;
    }

    umad_release_ca(&umad_ca);

    return 0;
}

int service_record_register_service(struct sr_ctx_t* context,
                                    const void* addr,
                                    size_t addr_size,
                                    const uint8_t (*service_key)[SR_128_BIT_SIZE],
                                    bool unregister_old_services) {
    struct sr_dev_service old_srs[SRS_MAX];
    struct sr_dev_service sr;
    int count, found;
    int ret;

    if (addr_size > SR_DEV_SERVICE_DATA_MAX - 1) {
        log_error("Unable to register service with data len %zu, max data len should be %d",
                  addr_size, SR_DEV_SERVICE_DATA_MAX - 1);
        return -EINVAL;
    }

    /* Register/replace new service */
    sr.id = context->service_id;
    strncpy(sr.name, context->service_name, sizeof(sr.name) - 1);
    sr.name[sizeof(sr.name) - 1] = '\0';
    sr.lease = context->sr_lease_time;
    memset(sr.data, 0,    sizeof(sr.data));
    sr.data[0] = (uint8_t)addr_size;
    memcpy(sr.data + 1, addr, addr_size);

    if ((ret = dev_register_service(context->dev, &sr, service_key)) < 0) {
        log_error("Couldn't register new SR (%d)", ret);
        return ret;
    } else {
        log_info("Registered new service, with id 0x%016" PRIx64, sr.id);
    }

    if (unregister_old_services) {
        /* Remove previous services, whose ID and port GID are not ours */
        do {
            count = dev_get_service(context, context->service_name, old_srs,
                                    SRS_MAX, context->sr_retries, 0);
            found = 0;
            for (int i = 0; i < count; ++i) {
                struct sr_dev_service* old_sr = &old_srs[i];

                if (old_sr->id == context->service_id &&
                        !memcmp(&old_sr->port_gid, &context->dev->port_gid,
                                sizeof(old_sr->port_gid))) {
                    continue;
                } else {
                    log_warning("Previous SR 0x%" PRIx64 " is"
                                "not the same as new SR 0x%" PRIx64 "",
                                old_sr->id, context->service_id);
                }

                found = 1;
                if ((ret = dev_unregister_service(context->dev, old_sr->id, old_sr->port_gid, service_key)) < 0) {
                    log_warning("Couldn't unregister old SR with id 0x%016" PRIx64 ": %s",
                                old_sr->id, strerror(ret));
                } else {
                    log_info("Unregistered old service with id 0x%016" PRIx64, old_sr->id);
                }
            }
        } while (found);
    }

    return 0;
}


int service_record_unregister_service(struct sr_ctx_t* context, const uint8_t (*service_key)[SR_128_BIT_SIZE]) {
    struct sr_dev_service old_srs[SRS_MAX];
    int result = 0;

    int count = dev_get_service(context, context->service_name, old_srs,
                                SRS_MAX, context->sr_retries, 0);

    for (int i = 0; i < count; ++i) {
        struct sr_dev_service* old_sr = &old_srs[i];

        if (old_sr->id == context->service_id) {
            int ret = dev_unregister_service(context->dev, old_sr->id, old_sr->port_gid, service_key);
            if (ret < 0) {
                log_warning("Couldn't unregister old SR with id 0x%016" PRIx64 ": %s", old_sr->id, strerror(ret));
                result++;
            } else {
                log_info("Unregistered old service with id 0x%016" PRIx64, old_sr->id);
            }
        }
    }

    return result;
}


int service_record_query_service(struct sr_ctx_t* context, struct sr_dev_service* srs,
                                 int srs_num, int retries) {
    int try = retries;

    if (retries < 0)
        try = SR_DEV_SERVICE_REGISTER_RETRIES;

    return dev_get_service(context, context->service_name, srs, srs_num, try, 0);
}

void service_record_printout_service(struct sr_dev_service* srs, int srs_num) {
    char buf[INET6_ADDRSTRLEN];

    log_info("SRs info:");
    for (int i = 0; i < srs_num; i++) {
        inet_ntop(AF_INET6, (void*)&(srs[i].port_gid), buf, sizeof(buf));
        log_info("%d) id=0x%016" PRIx64 " name=%s port_gid=%s lease=%dsec data=%p",
                 i, srs[i].id, srs[i].name, buf, srs[i].lease, srs[i].data);
        log_hex(srs[i].data, SR_DEV_SERVICE_DATA_MAX);
    }
}

static inline unsigned long get_timer(void) {
    struct timeval tv;
    int ret;

    do {
        ret = gettimeofday(&tv, NULL);
    } while (ret == -1 && errno == EINTR);

    return tv.tv_sec * 1000000ULL + tv.tv_usec;
}

int service_record_init(struct sr_ctx_t** context,
                        const char* service_name, uint64_t service_id,
                        const char* dev_name, int port, struct sr_config* conf) {
    struct sr_ctx_t* ctx = calloc(1, sizeof(struct sr_ctx_t));
    int ret = 0;

    if (!ctx) {
        return -ENOMEM;
    }

    ctx->dev = calloc(1, sizeof(struct sr_dev));
    if (!ctx->dev) {
        service_record_cleanup(ctx);
        *context = NULL;
        return -ENOMEM;
    }

    //    log_func = log_cb;

    if (conf) {
        ctx->sr_lease_time          = conf->sr_lease_time;
        ctx->sr_retries             = conf->sr_retries;
        ctx->dev->query_sleep       = conf->query_sleep;
        ctx->dev->sa_mkey           = conf->sa_mkey;
        ctx->dev->pkey              = conf->pkey;
        ctx->dev->fabric_timeout_ms = conf->fabric_timeout_ms;
        ctx->dev->pkey_index        = conf->pkey_index;
    } else {
        ctx->sr_lease_time          = SR_LEASE_TIME;
        ctx->sr_retries             = SR_RETRIES;
        ctx->dev->query_sleep       = SR_QUERY_SLEEP;
        ctx->dev->sa_mkey           = SA_MKEY;
        ctx->dev->pkey              = SR_DEV_PKEY;
        ctx->dev->fabric_timeout_ms = SA_FABRIC_TIMEOUT;
        ctx->dev->pkey_index        = 0;
    }
    ctx->dev->seed = get_timer();
    memset(ctx->dev->service_cache, 0, sizeof(ctx->dev->service_cache));
    ctx->service_name = strndup(service_name, SR_DEV_SERVICE_NAME_MAX);
    ctx->service_id = service_id;

    if ((ret = services_dev_init(ctx->dev, dev_name, port))) {
        service_record_cleanup(ctx);
        *context = NULL;
        return ret;
    }

    *context = ctx;

    return ret;
}

int service_record_init_via_guid(struct sr_ctx_t** context, const char* service_name, uint64_t service_id,
                                 uint64_t guid, struct sr_config* conf) {
    char hca[UMAD_CA_NAME_LEN];
    int port;

    if (guid2dev(guid, hca, &port)) {
        return 1;
    }

    return service_record_init(context, service_name, service_id, hca, port, conf);
}

int service_record_cleanup(struct sr_ctx_t* context) {
    if (context) {
        if (context->dev) {
            services_dev_cleanup(context->dev);
            free(context->dev);
        }

        free(context->service_name);
        free(context);
    }

    return 0;
}

