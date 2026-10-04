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

use clap::{Parser, Subcommand};
use ufmclient::{UFMConfig, UFMError};

mod create;
mod delete;
mod list;
mod version;
mod view;

#[derive(Parser)]
#[command(name = "ufm")]
#[command(version = "0.1.0")]
#[command(about = "UFM command line", long_about = None)]
struct Options {
    #[clap(long, env = "UFM_ADDRESS")]
    ufm_address: Option<String>,
    #[clap(long, env = "UFM_USERNAME")]
    ufm_username: Option<String>,
    #[clap(long, env = "UFM_PASSWORD")]
    ufm_password: Option<String>,
    #[clap(long, env = "UFM_TOKEN")]
    ufm_token: Option<String>,
    #[clap(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// View the detail of the partition
    View {
        /// The pkey of the partition to view
        #[arg(short, long)]
        pkey: String,
    },
    /// List all partitions
    List,
    /// Get the version of UFM
    Version,
    /// Delete the partition
    Delete {
        /// The pkey of the partition to delete
        #[arg(short, long)]
        pkey: String,
    },
    /// Create a partition
    Create {
        /// The pkey for the new partition
        #[arg(short, long)]
        pkey: String,
        /// The MTU of the new partition
        #[arg(long, default_value_t = 2048)]
        mtu: u16,
        /// The IPOverIB of the new partition
        #[arg(long, default_value_t = true)]
        ipoib: bool,
        /// The Index0 of the new partition
        #[arg(long, default_value_t = true)]
        index0: bool,
        /// The Membership of the new partition
        #[arg(short, long, default_value_t = String::from("full"))]
        membership: String,
        /// The ServiceLevel of the new partition
        #[arg(short, long, default_value_t = 0)]
        service_level: u8,
        /// The RateLimit of the new partition
        #[arg(short, long, default_value_t = 100.0)]
        rate_limit: f64,
        /// The GUIDs of the new partition
        #[arg(short, long)]
        guids: Vec<String>,
    },
}

#[tokio::main]
async fn main() -> Result<(), UFMError> {
    env_logger::init();

    let opt: Options = Options::parse();

    let conf = load_conf(&opt);
    match &opt.command {
        Some(Commands::Delete { pkey }) => delete::run(conf, pkey).await?,
        Some(Commands::Version) => version::run(conf).await?,
        Some(Commands::List) => list::run(conf).await?,
        Some(Commands::View { pkey }) => view::run(conf, pkey).await?,
        Some(Commands::Create {
            pkey,
            mtu,
            ipoib,
            index0,
            membership,
            service_level,
            rate_limit,
            guids,
        }) => {
            let opt = create::CreateOptions {
                pkey: pkey.to_string(),
                mtu: *mtu,
                ipoib: *ipoib,
                index0: *index0,
                membership: membership.to_string(),
                service_level: *service_level,
                rate_limit: *rate_limit,
                guids: guids.to_vec(),
            };
            create::run(conf, &opt).await?
        }
        None => {}
    };

    Ok(())
}

fn load_conf(opt: &Options) -> UFMConfig {
    let ufm_address = match opt.ufm_address.clone() {
        Some(s) => s,
        None => panic!("UFM_ADDRESS environment or ufm_address parameter not found"),
    };

    UFMConfig {
        address: ufm_address,
        username: opt.ufm_username.clone(),
        password: opt.ufm_password.clone(),
        token: opt.ufm_token.clone(),
    }
}
