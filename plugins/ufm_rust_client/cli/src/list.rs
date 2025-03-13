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

use ufmclient::{UFMConfig, UFMError};

pub async fn run(conf: UFMConfig) -> Result<(), UFMError> {
    let ufm = ufmclient::connect(conf)?;
    let ps = ufm.list_partition().await?;

    println!(
        "{:<15}{:<10}{:<10}{:<10}{:<10}{:<10}",
        "Name", "Pkey", "IPoIB", "MTU", "Rate", "Level"
    );

    for p in ps {
        println!(
            "{:<15}{:<10}{:<10}{:<10}{:<10}{:<10}",
            p.name,
            p.pkey.to_string(),
            p.ipoib,
            p.qos.mtu_limit,
            p.qos.rate_limit,
            p.qos.service_level
        )
    }

    Ok(())
}
