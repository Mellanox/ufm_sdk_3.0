/**
 * Copyright (C) Mellanox Technologies Ltd. 2016.  ALL RIGHTS RESERVED.
 *
 * See file LICENSE for terms.
 */

#include "service_record/services.h"

#include <inttypes.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

#include <infiniband/umad.h>
#include <infiniband/umad_types.h>
#include <infiniband/umad_sa.h>

#include "common/logger.h"

static int dev_sa_init(struct sr_dev* dev) {
    int err = 0;

    dev->portid = umad_open_port(dev->dev_name, dev->port_num);
    if (dev->portid < 0) {
        log_warning("Unable to get umad ca %s port %d. %m",
                    dev->dev_name, dev->port_num);
        err = -EADDRNOTAVAIL;
        goto out;
    }

    if ((dev->agent = umad_register(dev->portid, UMAD_CLASS_SUBN_ADM,
                                    UMAD_SA_CLASS_VERSION,
                                    UMAD_RMPP_VERSION, NULL)) < 0) {
        log_error("Unable to register UMAD_CLASS_SUBN_ADM");
        err = -errno;
        goto out_close_port;
    }

    log_info("Opened umad port to lid %u on %s port %d",
             dev->port_smlid, dev->dev_name, dev->port_num);
    goto out;

out_close_port:
    umad_close_port(dev->portid);
out:
    return err;
}

static int open_port(struct sr_dev* dev, int port) {
    umad_port_t umad_port;
    char* dev_name = NULL;
    int ret = 0;

    if (strcmp(dev->dev_name, "")) {
        dev_name = dev->dev_name;
    }

    if ((ret = umad_get_port(dev_name, port, &umad_port))) {
        dev->port_num = -1;
        log_error("Unable to get umad ca %s port %d. %m",
                  dev->dev_name, port);
        return ret;
    }

    if (umad_port.state != IBV_PORT_ACTIVE) {
        log_error("Port %d on %s is not active",
                  umad_port.portnum, dev->dev_name);
        umad_release_port(&umad_port);
        return -ENETDOWN;
    }

    if (!umad_port.sm_lid || umad_port.sm_lid > 0xBFFF) {
        log_error("No SM found for port %d on %s",
                  umad_port.portnum, dev->dev_name);
        umad_release_port(&umad_port);
        return -ECONNREFUSED;
    }

    dev->port_num = umad_port.portnum;
    dev->port_gid.global.subnet_prefix = umad_port.gid_prefix;
    dev->port_gid.global.interface_id  = umad_port.port_guid;
    dev->port_lid = umad_port.base_lid;
    dev->port_smlid = umad_port.sm_lid;
    strncpy(dev->dev_name, umad_port.ca_name, sizeof(dev->dev_name) - 1);
    dev->dev_name[sizeof(dev->dev_name) - 1] = '\0';

    log_info("port state: dev_name=%s port=%d state=%d phy_state=%d link_layer=%s",
             dev->dev_name, dev->port_num, umad_port.state,
             umad_port.phys_state, umad_port.link_layer);
    log_info("port lid=%u prefix=0x%" PRIx64 " guid=0x%" PRIx64,
             dev->port_lid,
             (uint64_t) __be64_to_cpu(dev->port_gid.global.subnet_prefix),
             (uint64_t) __be64_to_cpu(dev->port_gid.global.interface_id));

    if ((ret = umad_release_port(&umad_port))) {
        log_error("Unable to release %s port %d: %m",
                  dev->dev_name, umad_port.portnum);
        return ret;
    }

    /* Found active port with SM configured on this device */
    log_info("Using %s port %d", dev->dev_name, dev->port_num);

    return ret;
}

int services_dev_init(struct sr_dev* dev, const char* dev_name, int port) {
    char ca_names[UMAD_MAX_DEVICES][UMAD_CA_NAME_LEN];
    int num_devices;

    if ((num_devices = umad_get_cas_names(ca_names, UMAD_MAX_DEVICES)) < 0) {
        log_error("Unable to get CAs' list. %m");
        return -errno;
    }

    for (int i = 0; i < num_devices; i++) {
        if (!dev_name || !strlen(dev_name) ||
                !strcmp(ca_names[i], dev_name)) {
            if (dev_name) {
                strncpy(dev->dev_name, dev_name, sizeof(dev->dev_name) - 1);
                dev->dev_name[sizeof(dev->dev_name) - 1] = '\0';
            } else {
                strncpy(dev->dev_name, "", sizeof(dev->dev_name));
            }

            if (!open_port(dev, port) && !dev_sa_init(dev)) {
                return 0;
            }
        } else {
            log_info("Skipping device `%s', expected `%s'",
                     ca_names[i], dev_name);
        }
    }

    log_error("Unable to find appropriate CA device from %d devices", num_devices);
    return -ENODEV;
}

int services_dev_update(struct sr_dev* dev) {
    return open_port(dev, dev->port_num);
}

void services_dev_cleanup(struct sr_dev* dev) {
    umad_unregister(dev->portid, dev->agent);
    umad_close_port(dev->portid);
}
