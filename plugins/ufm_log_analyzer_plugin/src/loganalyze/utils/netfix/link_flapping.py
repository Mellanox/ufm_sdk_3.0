#
# Copyright © 2014-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
"""
This is the main logic for identifying flapping links
"""

from datetime import datetime
import traceback
import warnings

import pandas as pd
from loganalyze.utils.netfix.netfix_utils import (
    read_and_preprocessing_file,
    add_partner_info,
    add_link_hash_id,
)

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)


def _fill_missing_partner(df1, df2):
    df2["link_partner_node_guid"] = df2["link_partner_node_guid"].replace(
        "0x0000000000000000", ""
    )
    df2["link_partner_port_num"] = df2["link_partner_port_num"].replace(
        "0x0000000000000000", ""
    )
    df2["link_partner_port_num"] = df2["link_partner_port_num"].replace("0", 0)
    df2["link_partner_port_num"] = df2["link_partner_port_num"].replace("", 0)
    df2["link_partner_port_num"] = df2["link_partner_port_num"].replace(0.0, 0)
    df_join = pd.merge(
        left=df2,
        right=df1[
            [
                "Node_GUID",
                "Port_Number",
                "link_partner_node_guid",
                "link_partner_port_num",
            ]
        ],
        how="left",
        on=["Node_GUID", "Port_Number"],
    )
    df_join = df_join.rename(
        columns={
            "link_partner_node_guid_x": "link_partner_node_guid",
            "link_partner_port_num_x": "link_partner_port_num",
        }
    )
    df_join["link_partner_node_guid"] = (
        df_join["link_partner_node_guid"]
        .replace("", pd.NA)
        .fillna(df_join["link_partner_node_guid_y"])
        .replace(pd.NA, "")
    )
    df_join["link_partner_port_num"] = (
        df_join["link_partner_port_num"]
        .replace(0, pd.NA)
        .fillna(df_join["link_partner_port_num_y"])
        .replace(pd.NA, 0)
    )

    df_join = df_join.drop(
        columns=["link_partner_node_guid_y", "link_partner_port_num_y"]
    )
    return df_join


def _get_suspected_real_linkdown(
    df1_with_partner, df2_with_partner, min_to_filter_reboot_threshold=10
):
    func_summary_dict = {}
    col4diff_calc = [
        "Effective_Errors",
        "Symbol_Errors",
        "PortRcvDataExtended",
        "Link_Down",
        "Link_Down_partner",
    ]
    # relevant column to present
    col2_present = [
        "timestamp",
        "timestamp_partner",
        "Node_GUID",
        "Device_ID",
        "node_description",
        "Port_Number",
        "Device_ID_partner",
        "link_partner_description",
        "link_partner_node_guid",
        "link_partner_port_num",
        "Cable_SN",
        "Time_since_last_clear",
        "Time_since_last_clear_partner",
        "Total_Raw_BER",
        "Effective_BER",
        "Symbol_BER",
        "Total_Raw_BER_partner",
        "Effective_BER_partner",
        "Symbol_BER_partner",
        "max_time_since_clear_by_switch_or_server",
        "max_time_since_clear_by_switch_or_server_partner",
        "Status_Message",
        "local_reason_opcode",
        "remote_reason_opcode",
        "Status_Message_partner",
        "local_reason_opcode_partner",
        "remote_reason_opcode_partner",
        "estimated_time",
        "estimated_time_partner",
        "time_to_link_up_msec",
        "time_to_link_up_msec_partner",
    ] + col4diff_calc
    # take common columns
    col2_present1 = [col for col in col2_present if col in df1_with_partner.columns]
    col2_present1 = [col for col in col2_present1 if col in df2_with_partner.columns]

    join_iteration = pd.merge(
        df1_with_partner[col2_present1],
        df2_with_partner[col2_present1],
        how="inner",
        left_on=[
            "Node_GUID",
            "Port_Number",
            "link_partner_description",
            "link_partner_node_guid",
            "link_partner_port_num",
        ],
        right_on=[
            "Node_GUID",
            "Port_Number",
            "link_partner_description",
            "link_partner_node_guid",
            "link_partner_port_num",
        ],
    )
    # calculate diff columns
    for col in col4diff_calc:
        join_iteration["diff_" + col] = (
            join_iteration[col + "_y"] - join_iteration[col + "_x"]
        )

    # take the latest data to present
    col_y = [col + "_y" for col in col2_present1]
    col_latest = list(col2_present1)

    col_naming_dict = {}
    col_naming_dict = dict(zip(col_y, col_latest))

    join_iteration = join_iteration.rename(columns=col_naming_dict, errors="ignore")

    join_iteration = join_iteration.rename(
        columns={
            "timestamp_x": "prev_timestamp",
            "Link_Down_x": "prev_Link_Down",
            "Link_Down_partner_x": "prev_Link_Down_partner",
            "Time_since_last_clear_x": "prev_Time_since_last_clear",
            "Time_since_last_clear_partner_x": "prev_Time_since_last_clear_partner",
        },
        errors="ignore",
    )

    join_iteration = add_link_hash_id(join_iteration)
    join_iteration1 = join_iteration

    # remove old link down by estimated time
    join_iteration1 = join_iteration1[
        join_iteration1.estimated_time > join_iteration1.prev_timestamp
    ]

    join_iteration1["estimated_time"] = join_iteration1["estimated_time"].apply(
        lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
    )

    # add support of linkdown_diff<0 but linkdown value is >0
    df_linkdown = join_iteration1[
        (
            abs(
                join_iteration1.Time_since_last_clear
                - join_iteration1.Time_since_last_clear_partner
            )
            < 10
        )
        & (
            (join_iteration1.diff_Link_Down > 0)
            | ((join_iteration1.diff_Link_Down < 0) & (join_iteration1.Link_Down > 0))
        )
        & (
            (join_iteration1.diff_Link_Down_partner > 0)
            | (
                (join_iteration1.diff_Link_Down_partner < 0)
                & (join_iteration1.Link_Down_partner > 0)
            )
        )
        | (
            (join_iteration1.diff_Link_Down > 0)
            & (
                abs(
                    join_iteration1.Time_since_last_clear_partner
                    - join_iteration1.max_time_since_clear_by_switch_or_server_partner
                )
                > min_to_filter_reboot_threshold
            )
        )
        | (
            (join_iteration1.local_reason_opcode == 25)
            | (join_iteration1.remote_reason_opcode == 25)
        )
    ]

    if ("Device_ID" in df_linkdown.columns) & (
        "Device_ID_partner" in df_linkdown.columns
    ):
        df_linkdown["link_type"] = "other"
        mask = (df_linkdown.Device_ID.str.contains("Connect")) & (
            df_linkdown.Device_ID_partner.str.contains("Quantum")
        )
        df_linkdown.loc[mask, "link_type"] = "switch-hca"

        mask = (df_linkdown.Device_ID.str.contains("Quantum")) & (
            df_linkdown.Device_ID_partner.str.contains("Connect")
        )
        df_linkdown.loc[mask, "link_type"] = "switch-hca"

        mask = (df_linkdown.Device_ID.str.contains("Quantum")) & (
            df_linkdown.Device_ID_partner.str.contains("Quantum")
        )
        df_linkdown.loc[mask, "link_type"] = "switch-switch"

    # use /2 because table have duplication A->B + B->A
    func_summary_dict["Number of links - suspected linkdown switch-switch"] = (
        df_linkdown[df_linkdown["link_type"] == "switch-switch"]
        .link_hash_id.drop_duplicates()
        .shape[0]
    )
    func_summary_dict["Number of links - suspected linkdown switch-hca"] = (
        df_linkdown[df_linkdown["link_type"] == "switch-hca"]
        .link_hash_id.drop_duplicates()
        .shape[0]
    )

    number_active_links = df2_with_partner[
        df2_with_partner.Phy_Manager_State == "Active"
    ].shape[0]
    number_link_down = df_linkdown.shape[0]
    func_summary_dict["pct of link down"] = round(
        100 * number_link_down / number_active_links, 2
    )
    # set_df_col_order
    col_order = (
        ["link_hash_id", "link_type"]
        + list(df2_with_partner.columns)
        + [
            "diff_Link_Down",
            "diff_Link_Down_partner",
            "prev_Link_Down",
            "prev_Link_Down_partner",
            "prev_Time_since_last_clear",
            "prev_Time_since_last_clear_partner",
            "estimated_time",
        ]
    )

    col_order1 = [col for col in col_order if col in df_linkdown.columns]
    df_linkdown = df_linkdown[col_order1]

    return df_linkdown, func_summary_dict


def get_link_flapping(prev_counters_csv, cur_counters_csv):
    """
    Entry point to the flapping links logic.
    Gets 2 telemetry sampling and returns a dataframe
    with flapping links
    """
    try:
        df1 = read_and_preprocessing_file(prev_counters_csv)
        df2 = read_and_preprocessing_file(cur_counters_csv)

        # complete missing partner in df2 based on df1
        df2 = _fill_missing_partner(df1, df2)
        df1_with_partner = add_partner_info(df1)
        df2_with_partner = add_partner_info(df2)

        # linkdown both sides
        linkdown_df1, _ = _get_suspected_real_linkdown(
            df1_with_partner, df2_with_partner, min_to_filter_reboot_threshold=10
        )
        return linkdown_df1
    except Exception as e:
        print(e)
        traceback.print_exc()
        return pd.DataFrame()
