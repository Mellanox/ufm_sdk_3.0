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

use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use thiserror::Error;
use url::Url;

use self::port::{PhysicalPort, Port, VirtualPort};
use self::rest::{RestClient, RestClientConfig, RestError, RestScheme};

mod port;
mod rest;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PartitionQoS {
    // Default 2k; one of 2k or 4k; the MTU of the services.
    pub mtu_limit: u16,
    // Default is None, value can be range from 0-15
    pub service_level: u8,
    // Default is None, can be one of the following: 2.5, 10, 30, 5, 20, 40, 60, 80, 120, 14, 56, 112, 168, 25, 100, 200, or 300
    pub rate_limit: f64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
pub enum PortMembership {
    Limited,
    Full,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PortConfig {
    /// The GUID of Port.
    pub guid: String,
    /// Default false; store the PKey at index 0 of the PKey table of the GUID.
    pub index0: bool,
    /// Default is full:
    ///   "full"    - members with full membership can communicate with all hosts (members) within the network/partition
    ///   "limited" - members with limited membership cannot communicate with other members with limited membership.
    ///               However, communication is allowed between every other combination of membership types.
    pub membership: PortMembership,
}

#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
pub struct PartitionKey(i32);

impl PartitionKey {
    pub fn is_default_pkey(&self) -> bool {
        self.0 == 0x7fff
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Partition {
    /// The name of Partition.
    pub name: String,
    /// The pkey of Partition.
    pub pkey: PartitionKey,
    /// Default false
    pub ipoib: bool,
    /// The QoS of Partition.
    pub qos: PartitionQoS,
}

#[derive(Serialize, Deserialize, Debug)]
struct Pkey {
    pkey: String,
    ip_over_ib: bool,
    membership: PortMembership,
    index0: bool,
    guids: Vec<String>,
}

impl TryFrom<i32> for PartitionKey {
    type Error = UFMError;

    fn try_from(pkey: i32) -> Result<Self, Self::Error> {
        if pkey != (pkey & 0x7fff) {
            return Err(UFMError::InvalidPKey(pkey.to_string()));
        }

        Ok(PartitionKey(pkey))
    }
}

impl TryFrom<String> for PartitionKey {
    type Error = UFMError;

    fn try_from(pkey: String) -> Result<Self, Self::Error> {
        let p = pkey.trim_start_matches("0x");
        let k = i32::from_str_radix(p, 16);

        match k {
            Ok(v) => Ok(PartitionKey(v)),
            Err(_e) => Err(UFMError::InvalidPKey(pkey.to_string())),
        }
    }
}

impl TryFrom<&String> for PartitionKey {
    type Error = UFMError;

    fn try_from(pkey: &String) -> Result<Self, Self::Error> {
        PartitionKey::try_from(pkey.to_string())
    }
}

impl TryFrom<&str> for PartitionKey {
    type Error = UFMError;

    fn try_from(pkey: &str) -> Result<Self, Self::Error> {
        PartitionKey::try_from(pkey.to_string())
    }
}

impl ToString for PartitionKey {
    fn to_string(&self) -> String {
        format!("0x{:x}", self.0)
    }
}

impl From<PartitionKey> for i32 {
    fn from(v: PartitionKey) -> i32 {
        v.0
    }
}

impl TryFrom<String> for PortMembership {
    type Error = UFMError;

    fn try_from(membership: String) -> Result<Self, Self::Error> {
        match membership.to_lowercase().as_str() {
            "full" => Ok(PortMembership::Full),
            "limited" => Ok(PortMembership::Limited),
            _ => Err(UFMError::InvalidConfig("invalid membership".to_string())),
        }
    }
}

impl TryFrom<&str> for PortMembership {
    type Error = UFMError;

    fn try_from(membership: &str) -> Result<Self, Self::Error> {
        PortMembership::try_from(membership.to_string())
    }
}

pub struct Ufm {
    client: RestClient,
}

#[derive(Error, Debug)]
pub enum UFMError {
    #[error("{0}")]
    Unknown(String),
    #[error("'{0}' not found")]
    NotFound(String),
    #[error("invalid pkey '{0}'")]
    InvalidPKey(String),
    #[error("invalid configuration '{0}'")]
    InvalidConfig(String),
}

impl From<RestError> for UFMError {
    fn from(e: RestError) -> Self {
        match e {
            RestError::Unknown(msg) => UFMError::Unknown(msg),
            RestError::NotFound(msg) => UFMError::NotFound(msg),
            RestError::AuthFailure(msg) => UFMError::InvalidConfig(msg),
            RestError::InvalidConfig(msg) => UFMError::InvalidConfig(msg),
        }
    }
}

pub struct UFMConfig {
    pub address: String,
    pub username: Option<String>,
    pub password: Option<String>,
    pub token: Option<String>,
}

pub fn connect(conf: UFMConfig) -> Result<Ufm, UFMError> {
    let addr = Url::parse(&conf.address)
        .map_err(|_| UFMError::InvalidConfig("invalid UFM url".to_string()))?;
    let address = addr
        .host_str()
        .ok_or(UFMError::InvalidConfig("invalid UFM host".to_string()))?;

    let (base_path, auth_info) = match &conf.token {
        None => {
            let password = conf
                .password
                .clone()
                .ok_or(UFMError::InvalidConfig("password is empty".to_string()))?;
            let username = conf
                .username
                .clone()
                .ok_or(UFMError::InvalidConfig("username is empty".to_string()))?;

            (
                "/ufmRest".to_string(),
                base64::encode(format!("{}:{}", username, password)),
            )
        }
        Some(t) => ("/ufmRestV3".to_string(), t.to_string()),
    };

    let c = RestClient::new(&RestClientConfig {
        address: address.to_string(),
        port: addr.port(),
        auth_info,
        base_path,
        scheme: RestScheme::from(addr.scheme().to_string()),
    })?;

    Ok(Ufm { client: c })
}

impl Ufm {
    pub async fn bind_ports(&self, p: Partition, ports: Vec<PortConfig>) -> Result<(), UFMError> {
        let path = String::from("/resources/pkeys");

        let mut membership = PortMembership::Full;
        let mut index0 = true;

        let mut guids = vec![];
        for pb in ports {
            membership = pb.membership.clone();
            index0 = pb.index0;
            guids.push(pb.guid.to_string());
        }

        let pkey = Pkey {
            pkey: p.pkey.clone().to_string(),
            ip_over_ib: p.ipoib,
            membership,
            index0,
            guids,
        };

        let data = serde_json::to_string(&pkey)
            .map_err(|_| UFMError::InvalidConfig("invalid partition".to_string()))?;

        self.client.post(&path, data).await?;

        Ok(())
    }

    pub async fn unbind_ports(
        &self,
        pkey: PartitionKey,
        guids: Vec<String>,
    ) -> Result<(), UFMError> {
        let path = String::from("/actions/remove_guids_from_pkey");

        #[derive(Serialize, Deserialize, Debug)]
        struct Pkey {
            pkey: String,
            guids: Vec<String>,
        }

        let pkey = Pkey {
            pkey: pkey.clone().to_string(),
            guids,
        };

        let data = serde_json::to_string(&pkey)
            .map_err(|_| UFMError::InvalidConfig("invalid partition".to_string()))?;

        self.client.post(&path, data).await?;

        Ok(())
    }

    pub async fn get_partition(&self, pkey: &str) -> Result<Partition, UFMError> {
        let pkey = PartitionKey::try_from(pkey)?;

        let path = format!("/resources/pkeys/{}?qos_conf=true", pkey.to_string());

        #[derive(Serialize, Deserialize, Debug)]
        struct Pkey {
            partition: String,
            ip_over_ib: bool,
            qos_conf: PartitionQoS,
        }
        let pk: Pkey = self.client.get(&path).await?;

        Ok(Partition {
            name: pk.partition,
            pkey,
            ipoib: pk.ip_over_ib,
            qos: pk.qos_conf,
        })
    }

    pub async fn list_partition(&self) -> Result<Vec<Partition>, UFMError> {
        #[derive(Serialize, Deserialize, Debug)]
        struct Pkey {
            partition: String,
            ip_over_ib: bool,
            qos_conf: PartitionQoS,
        }

        let path = String::from("/resources/pkeys?qos_conf=true");
        let pkey_qos: HashMap<String, Pkey> = self.client.list(&path).await?;

        let mut parts = Vec::new();

        for (k, v) in pkey_qos {
            parts.push(Partition {
                name: v.partition,
                pkey: PartitionKey::try_from(&k)?,
                ipoib: v.ip_over_ib,
                qos: v.qos_conf.clone(),
            });
        }

        Ok(parts)
    }

    pub async fn delete_partition(&self, pkey: &str) -> Result<(), UFMError> {
        let path = format!("/resources/pkeys/{}", pkey);
        self.client.delete(&path).await?;

        Ok(())
    }

    pub async fn list_port(&self, pkey: PartitionKey) -> Result<Vec<Port>, UFMError> {
        let mut res = Vec::new();
        // get GUIDs from pkey
        #[derive(Serialize, Deserialize, Debug)]
        struct PkeyWithGUIDs {
            pub partition: String,
            pub ip_over_ib: bool,
            pub guids: Vec<PortConfig>,
        }

        let path = format!("resources/pkeys/{}?guids_data=true", pkey.to_string());
        let pkeywithguids: PkeyWithGUIDs = self.client.get(&path).await?;

        // list physical ports
        let path = String::from("/resources/ports?sys_type=Computer");
        let physical_ports: Vec<PhysicalPort> = self.client.list(&path).await?;

        // list virtual ports
        let path = String::from("/resources/vports");
        let virtual_ports: Vec<VirtualPort> = self.client.list(&path).await?;

        let mut port_map = HashMap::new();
        for pport in physical_ports {
            port_map.insert(pport.guid.clone(), Port::from(pport));
        }
        for vport in virtual_ports {
            port_map.insert(vport.virtual_port_guid.clone(), Port::from(vport));
        }

        if !pkey.is_default_pkey() {
            for port_config in pkeywithguids.guids {
                let guid = port_config.guid;
                match port_map.get(&guid) {
                    Some(p) => {
                        res.push(p.clone());
                    }
                    None => {
                        let p = Port {
                            guid,
                            name: None,
                            system_id: "".to_string(),
                            lid: 65535,
                            system_name: "".to_string(),
                            logical_state: "Unknown".to_string(),
                            parent_guid: None,
                            port_type: None,
                        };
                        res.push(p);
                    }
                }
            }
        } else {
            // list all the ports for default pkey(0x7fff)
            res = port_map.values().cloned().collect();
        }
        Ok(res)
    }

    pub async fn version(&self) -> Result<String, UFMError> {
        #[derive(Serialize, Deserialize, Debug)]
        struct Version {
            ufm_release_version: String,
        }

        let path = String::from("/app/ufm_version");
        let v: Version = self.client.get(&path).await?;

        Ok(v.ufm_release_version)
    }
}
