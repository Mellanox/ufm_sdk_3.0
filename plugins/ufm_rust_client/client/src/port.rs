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

use std::fmt::Display;

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
pub enum PortType {
    Physical,
    Virtual,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
pub struct Port {
    pub guid: String,
    pub name: Option<String>,
    pub system_id: String,
    pub lid: i32,
    pub system_name: String,
    pub logical_state: String,
    pub parent_guid: Option<String>,
    pub port_type: Option<PortType>,
}

impl Display for Port {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let name = match self.name.clone() {
            Some(n) => n,
            None => "".to_string(),
        };
        let parent_guid = match self.parent_guid.clone() {
            Some(p) => p,
            None => "".to_string(),
        };
        let port_type = match self.port_type {
            Some(PortType::Physical) => "physical".to_string(),
            Some(PortType::Virtual) => "virtual".to_string(),
            None => "".to_string(),
        };
        write!(
            f,
            "    {:<20}{:<20}{:<10}{:<20}{:<10}{:<15}{:<10}{:<20}",
            self.guid,
            parent_guid,
            port_type,
            self.system_id,
            self.lid,
            self.system_name,
            self.logical_state,
            name,
        )
    }
}

impl From<PhysicalPort> for Port {
    fn from(physicalport: PhysicalPort) -> Self {
        Port {
            guid: physicalport.guid.clone(),
            name: Some(physicalport.name),
            system_id: physicalport.system_id,
            lid: physicalport.lid,
            system_name: physicalport.system_name,
            logical_state: physicalport.logical_state,
            parent_guid: None,
            port_type: Some(PortType::Physical),
        }
    }
}

impl From<VirtualPort> for Port {
    fn from(virtualport: VirtualPort) -> Self {
        Port {
            guid: virtualport.virtual_port_guid.clone(),
            name: None,
            system_id: virtualport.system_guid,
            lid: virtualport.virtual_port_lid,
            system_name: virtualport.system_name,
            logical_state: virtualport.virtual_port_state,
            parent_guid: Some(virtualport.port_guid),
            port_type: Some(PortType::Virtual),
        }
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PhysicalPort {
    pub guid: String,
    pub name: String,
    #[serde(rename = "systemID")]
    pub system_id: String,
    pub lid: i32,
    pub system_name: String,
    pub logical_state: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct VirtualPort {
    pub virtual_port_guid: String,
    pub system_guid: String,
    pub virtual_port_lid: i32,
    pub system_name: String,
    pub virtual_port_state: String,
    pub port_guid: String,
}
