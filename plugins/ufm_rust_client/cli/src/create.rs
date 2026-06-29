/*
 * Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
 *
 * This software product is a proprietary product of Nvidia Corporation and its affiliates
 * (the "Company") and all right, title, and interest in and to the software product,
 * including all associated intellectual property rights, are and shall
 * remain exclusively with the Company.
 *
 * This software product is governed by the End User License Agreement
 * provided with the software product.
 */


use ufmclient::{
    Partition, PartitionKey, PartitionQoS, PortConfig, PortMembership, UFMConfig, UFMError,
};

pub struct CreateOptions {
    pub pkey: String,
    pub mtu: u16,
    pub ipoib: bool,
    pub index0: bool,
    pub membership: String,
    pub service_level: u8,
    pub rate_limit: f64,
    pub guids: Vec<String>,
}

pub async fn run(conf: UFMConfig, opt: &CreateOptions) -> Result<(), UFMError> {
    let ufm = ufmclient::connect(conf)?;

    let mut pbs = vec![];
    for g in &opt.guids {
        pbs.push(PortConfig {
            guid: g.to_string(),
            index0: opt.index0,
            membership: PortMembership::try_from(opt.membership.clone())?,
        })
    }

    let p = Partition {
        name: "".to_string(),
        pkey: PartitionKey::try_from(opt.pkey.clone())?,
        ipoib: opt.ipoib,
        qos: PartitionQoS {
            mtu_limit: opt.mtu,
            service_level: opt.service_level,
            rate_limit: opt.rate_limit,
        },
    };

    ufm.bind_ports(p, pbs).await?;

    Ok(())
}
