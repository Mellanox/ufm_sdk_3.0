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
from enum import Enum
import pandas as pd
import numpy as np
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype


class FileSource(Enum):
    UFM  = "ufm"
    collectx = "collectx"

Phy_Manager_State_dict_str = {
                        'Active_or_Linkup': 'Active',                      
                        'Rx_disable': 'RX_DISABLE'                  ''
                        }

link_down_opcode_dict = { 0:'No_link_down_indication',
1:'Unknown_reason',
2:'Hi_SER_or_Hi_BER',
3:'Block_Lock_loss',
4:'Alignment_loss',
5:'FEC_sync_loss',
6:'PLL_lock_loss',
7:'FIFO_overflow',
8:'false_SKIP_condition',
9:'Minor_Error_threshold_exceeded',
10:'Physical_layer_retransmission_timeout',
11:'Heartbeat_errors',
12:'Link_Layer_credit_monitoring_watchdog',
13:'Link_Layer_integrity_threshold_exceeded',
14:'Link_Layer_buffer_overrun',
15:'Down_by_outband_command_with_healthy_link',
16:'Down_by_outband_command_for_link_with_hi_ber',
17:'Down_by_inband_command_with_healthy_link',
18:'Down_by_inband_command_for_link_with_hi_ber',
19:'Down_by_verification_GW',
20:'Received_Remote_Fault',
21:'Received_TS1',
22:'Down_by_management_command',
23:'Cable_was_unplugged',
24:'Cable_access_issue',
25:'Thermal_shutdown',
26:'Current_issue',
27:'Power_budget',
28:'Fast_recovery_raw_ber',
29:'Fast_recovery_effective_ber',
30:'Fast_recovery_symbol_ber',
31:'Fast_recovery_credit_watchdog',
32:'Timeout'}


global Phy_Manager_State_dict
Phy_Manager_State_dict = {0:'Disabled',
                        2: 'Polling',
                        3: 'Active',
                        4: 'Close',
                        5: 'ETH_PHY_UP',
                        7: 'RX_DISABLE'
                        }

global switch_dict 
switch_dict= {
            '0x0': "UNKNOWN",
            '0xC738': "SwitchX and SwitchX-2",  # Baz
            '0x0246': "SwitchX in Flash Recovery Mode",
            '0xCB20': "Switch-IB",  # Pelican
            '0x0247': "Switch-IB in Flash Recovery Mode",
            '0xCB84': "Spectrum",  # Condor
            '0x0249': "Spectrum in Flash Recovery Mode",
            '0xCF08': "Switch-IB 2",  # Eagle
            '0x024B': "Switch-IB 2 in Flash Recovery Mode",
            '0xD2F0': "Quantum",  # Raven
            '0x024D': "Quantum in Flash Recovery Mode",
            '0xCF6C': "Spectrum-2",  # Phoenix
            '0x024E': "Spectrum-2 in Flash Recovery Mode",
            '0x024F': "Spectrum-2 in Secure Flash Recovery Mode (obsolete) [Internal]",
            '0xCF70': "Spectrum-3",  # Firebird
            '0x0250': "Spectrum-3 in Flash Recovery Mode",
            '0x0251': "Spectrum-3 in Secure Flash Recovery Mode (obsolete) [Internal]",
            '0x0252': "Spectrum-3 Amos GearBox [Internal]",  # Amos
            '0x0253': "AGBM - Amos GearBox Manager",
            '0xCF80': "Spectrum-4 Spectrum-4",  # Albatross
            '0x0254': "Spectrum-4 in Flash Recovery Mode",
            '0x0255': "Spectrum-4 RMA [Internal]",
            '0x0256': "Abir GearBox",  # Abir
            '0x0357': "Abir GearBox in Flash Recovery Mode",
            '0x0358': "Abir GearBox in RMA",
            '0xD2F2': "Quantum-2",  # Blackbird
            '0x0257': "Quantum-2 in Flash Recovery Mode",
            '0x0258': "Quantum-2 RMA"}


global hca_dict 
hca_dict = {4099: "ConnectX-3",
            4113: "Connect-IB",
            4115: "ConnectX-4",
            4117: "ConnectX-4 Lx",
            4119: "ConnectX-5",
            4121: "ConnectX-5 Ex",
            4123: "ConnectX-6",
            4125: "ConnectX-6 Dx",
            4129: "Connectx-7",
            41680: "BlueField with crypto enabled",
            41681: "BlueField with crypto disabled",
            41684: "BlueField-2 with crypto enabled",
            41685: "BlueField-2 with crypto disabled",
            41686: "BlueField-2 integrated ConnectX-6 Dx network controller",
            41690: "BlueField-3 SoC Crypto enabled",
            41691: "BlueField-3 SoC Crypto disabled",
            41692: "BlueField-3 integrated ConnectX-7 network controller",
            53001: "Aggregation Node"
        }

def read_and_preprocessing_file(file_path:str):
    
    df_file = pd.read_csv(file_path, encoding = "ISO-8859-1")

    if df_file.shape[0]==0:
        print (' ERROR: empty file - ',file_path)

    df_file = df_file.rename(columns={'Node_Description': 'node_description'})

    df_file = df_file[df_file.node_description !='Mellanox Technologies Aggregation Node']

    if ('ts' in df_file.columns) :         
        df_file = df_file.drop(columns=['timestamp'], errors='ignore')
        df_file = df_file.rename(columns={'ts': 'timestamp'})

    # remove non numeric timestamp - remove all row
    df_file.timestamp =  pd.to_numeric(df_file.timestamp, errors='coerce')
    df_file = df_file.dropna(subset=['timestamp'])
    # if timestamp in milisec divid by 1000
    if len(str(df_file['timestamp'].iloc[0]))>15:
        df_file['timestamp'] = df_file['timestamp']/1000000
    else :
        df_file['timestamp'] = df_file['timestamp']/1000


    # check if a link appear more than once and need to take only one timestamp
    num_iterations  = df_file.groupby(['Node_GUID','Port_Number']).agg({'timestamp':'nunique'}).reset_index().timestamp.max()
    if num_iterations>1:
        file_type = FileSource.collectx
    else:
        file_type = FileSource.UFM
        df_file['timestamp'] = min(df_file.timestamp)

    # select one timestamp from the file
    if (file_type == FileSource.collectx) & (df_file.timestamp.drop_duplicates().shape[0] >1) :
        date_to_use = np.sort(df_file['timestamp'].unique())[-2]
        df_file = df_file[df_file.timestamp==date_to_use]

    # features handeling
    if ('Temperature' in df_file.columns):
        if (is_string_dtype(df_file['Temperature'])) & (len(pd.unique(df_file['Temperature']))>1):
            df_file.Temperature = df_file.Temperature.str.replace('C','').astype('float')

    #time since last clear
    df_file = df_file.rename(columns={'Time_since_last_clear_Min': 'Time_since_last_clear'})   
    df_file = df_file.rename(columns={'Time_since_last_clear__Min_': 'Time_since_last_clear'})
    df_file = df_file.rename(columns={'Time_since_last_clear_[Min]': 'Time_since_last_clear'})

    df_file ['estimated_time'] = df_file['timestamp'] - 60*df_file['Time_since_last_clear']
    
    # check basic columns that must exists
    must_columns_in_files = ['Node_GUID','Port_Number','timestamp','Time_since_last_clear','link_partner_node_guid','link_partner_port_num','Link_Down']
    for col in must_columns_in_files:
        if (col in df_file.columns) ==False:
            print (col, ' is missing in data !!!')

    df_file = df_file[df_file.Port_Number != 65]

    switch_dict1 = {int(k,16): v for k, v in switch_dict.items()}
    hca_dict1 = {k: v for k, v in hca_dict.items()}
    df_file = df_file.replace({'Device_ID':hca_dict1})
    df_file = df_file.replace({'Device_ID':switch_dict1})

    df_file = df_file.replace({'Phy_Manager_State':Phy_Manager_State_dict})
    df_file = df_file.replace({'Phy_Manager_State':Phy_Manager_State_dict_str})

    # replace strings in opcode by numbers
    opcode_dict = {v: k for k, v in link_down_opcode_dict.items()}
    df_file = df_file.replace({'local_reason_opcode':opcode_dict})
    df_file = df_file.replace({'remote_reason_opcode':opcode_dict})

    # to add in the future - now will need change in other places
    # if df_file.local_reason_opcode.str.is_numeric_dtype: 
    #     df_file = df_file.replace({'local_reason_opcode':link_down_opcode_dict})
    #     df_file = df_file.replace({'remote_reason_opcode':link_down_opcode_dict})
    
    if 'time_to_link_up_ext_msec' in df_file.columns:
        df_file = df_file.rename(columns = {'time_to_link_up_ext_msec':'time_to_link_up_msec'})

    col_to_convert_to_float = ['Link_Down','Symbol_BER','Effective_BER','Port_Number',
                               'PortXmitDiscards','link_partner_port_num','max_delta_freq_0','max_delta_freq_1']


    for col in   col_to_convert_to_float:
        if col in df_file.columns:
            df_file[col] = pd.to_numeric(df_file[col], errors="coerce")
            df_file.dropna(subset=[col], inplace=True)
        else:
            print (col, ' not exists in dataframe') 

    # add to df min /max/std of time since lase clear per switch/host name + add 'server_name' col
    df_file = get_time_since_last_clear_per_groups(df_file)

    df_file = df_file.replace({'Phy_Manager_State':{'0':'Disabled', '2':'Polling','3':'Active',
                                          '4':'Close', '5':'ETH_PHY_UP','7':'RX_DISABLE'}})
    
    # drop columns that all is nan - relevant for meta which have 2 fw_version columns
    df_file.dropna(how='all', axis=1, inplace=True) 


    return df_file

def get_time_since_last_clear_per_groups (df):

    df['server_name'] = ''
    if is_numeric_dtype(df.Device_ID.dtype):
        mask = (df.Device_ID.astype(float).astype('Int64').isin(list(hca_dict.keys()))) 
    else:
        mask = (df.Device_ID.astype(str).str.contains('Connect'))

    if  not 'Time_since_last_clear' in df.columns:
        print (' Time_since_last_clear not exists in df ')
        return df
    
    # mask = ((df.Device_ID.astype(float).astype('Int64').isin(list(hca_dict.keys()))) | (df.Device_ID.astype(str).str.contains('Connect')))
    df.loc[mask,'server_name'] = df.loc[mask,'node_description'].apply(lambda x: x.split(' ')[0] )



    df_hca = df[mask]    
    df_hca_group = df_hca.groupby('server_name').agg({'Time_since_last_clear':['min','max','std']})
    df_hca_group = df_hca_group.reset_index()
    df_hca_group.columns = ['server_name','min_Time_since_last_clear_server','max_Time_since_last_clear_server','std_Time_since_last_clear_server']

    switch_dict1 = {int(k,16): v for k, v in switch_dict.items()}

    if is_numeric_dtype(df.Device_ID.dtype):
        (df.Device_ID.astype(float).astype('Int64').isin(list(switch_dict1.keys())))
    else:
        mask = (df.Device_ID.astype(str).str.contains('Quantum'))

    df_switch= df[mask]
    df_switch_group = df_switch.groupby('Node_GUID').agg({'Time_since_last_clear':['min','max','std']})
    df_switch_group = df_switch_group.reset_index()
    df_switch_group.columns = ['Node_GUID','min_Time_since_last_clear_switch','max_Time_since_last_clear_switch','std_Time_since_last_clear_switch']

    df_join1 = pd.merge (left = df, right=df_hca_group, left_on=['server_name'], right_on=['server_name'], how = 'left')
    df_join2 = pd.merge (left = df_join1, right=df_switch_group, left_on=['Node_GUID'], right_on=['Node_GUID'], how = 'left')

    df_join2 ['max_time_since_clear_by_switch_or_server']= df_join2[['max_Time_since_last_clear_switch','max_Time_since_last_clear_server']].max(axis=1)

    # delete unused columns for now


    df_join2 ['change_from_max_switch_or_server'] =  df_join2['max_time_since_clear_by_switch_or_server']- df_join2['Time_since_last_clear']
    df_join2['guid_and_port'] = df_join2['Node_GUID']+'_'+df_join2['Port_Number'].astype(str)
    df_join2_group  = df_join2[df_join2.change_from_max_switch_or_server < 10].groupby(['server_name','Node_GUID']).agg({'guid_and_port':'nunique'})
    df_join2_group = df_join2_group.reset_index()
    df_join2_group.columns = ['server_name','Node_GUID','num_ports_in_last_switch_or_server_reboot']

    df_join2 = pd.merge(left = df_join2, right = df_join2_group, how = 'left', on = ['server_name','Node_GUID'])

    df_join2 = df_join2.drop(columns=['min_Time_since_last_clear_switch', 'std_Time_since_last_clear_switch','min_Time_since_last_clear_server','std_Time_since_last_clear_server','guid_and_port'], errors='ignore')

    return df_join2

def add_partner_info(df_file, use_all_columns_flag = False,ignore_server_list= []):


    # filter out on purpose reboot 
    # 15 Down_by_outband_command_with_healthy_link
    # 17 Down_by_inband_command_with_healthy_link
    # 22 Down_by_management_command
    # 23 .Cable_was_unplugged

    # df_link_down = sqldf("select * \
    #     from df_file \
    #     where link_partner_description <>''\
    #      and remote_reason_opcode not in (15,17,22,23)\
    #     and local_reason_opcode not in (15,17,22,23)" )
    #    print ('Number of unique linkdown Node_GUID+Port_Number filterd by opcode ',df_link_down[df_link_down.Link_Down_diff>0][['Node_GUID','Port_Number']].drop_duplicates().shape[0])
  
    # dont ignore opcode
    df_link_down = df_file
                         
 
    if use_all_columns_flag :
        columns_to_display = df_link_down.columns
    else:
        columns_to_display = ['timestamp','layer','Device_ID', 'Cable_SN','Cable_PN','FW_Version','cable_fw_version','Node_GUID','Port_Number','node_description','layer','server_name','Link_Down','link_partner_node_guid','link_partner_port_num',\
                                                                'link_partner_description','Total_Raw_BER','Effective_BER','Symbol_BER','Time_since_last_clear','sw_revision',
                                                                'Effective_Errors','Symbol_Errors','PortRcvDataExtended',\
                                                                'max_time_since_clear_by_switch_or_server', 'Status_Message','local_reason_opcode',	'remote_reason_opcode','Phy_Manager_State','estimated_time', 'estimated_time_partner',\
                                                                    'time_to_link_up_msec','time_to_link_up_msec_partner'
                                                                    ] + [col for col in df_link_down if ('_power_lane' in col.lower())]
    

    columns_to_display0 = [col for col in columns_to_display if col in df_file.columns]
    columns_to_display1 = [col for col in columns_to_display0 if col not in ['layer_partner']]
    columns_to_display1 = list(set(columns_to_display1))

        # add number of link down to the partner to maybe the partner is problematic
    df_link_down_with_partner_link_rows = pd.merge(df_link_down[columns_to_display1 ], \
                                                df_link_down[columns_to_display1],  \
                                                how='inner', left_on=['link_partner_node_guid','link_partner_port_num'], right_on = ['Node_GUID','Port_Number'])

    col_x = [col+'_x' for col in columns_to_display1]
    col_local = [col for col in columns_to_display1]

    col_y = [col+'_y' for col in columns_to_display1]
    col_partner = [col+'_partner' for col in columns_to_display1]

    col_naming_dict = {}
    col_naming_dict = dict(zip(col_x+col_y, col_local+col_partner))

    df_link_down_with_partner_link_rows = df_link_down_with_partner_link_rows.rename(columns = col_naming_dict)

    # col_x = [col+'_x' for col in columns_to_display1]
    # col_y = [col+'_y' for col in columns_to_display1]

    df_link_down_with_partner_link_rows = df_link_down_with_partner_link_rows.rename(columns = col_naming_dict)
    df_link_down_with_partner_link_rows1 = df_link_down_with_partner_link_rows

    if len(ignore_server_list)>0:
        df_link_down_with_partner_link_rows1 = df_link_down_with_partner_link_rows1[~df_link_down_with_partner_link_rows1.server_name_partner.isin(ignore_server_list)]

    # set_df_col_order 
    col_order = list(df_file.columns) + [col +'_partner' for col in df_file]
    
    col_order1 = [col for col in col_order if col in df_link_down_with_partner_link_rows1.columns]
    df_link_down_with_partner_link_rows1 = df_link_down_with_partner_link_rows1[col_order1]

    return df_link_down_with_partner_link_rows1

def add_link_hash_id(join_iteration):
    join_iteration ['link_hash_id']  = join_iteration.apply(lambda x: min(x['Node_GUID'],x['link_partner_node_guid']) + '_'+\
                                                                    max(x['Node_GUID'],x['link_partner_node_guid']) +   '_'+\
                                                                        min(str(int(x['Port_Number'])),str(int(x['link_partner_port_num'])))+'_'+\
                                                                        max(str(int(x['Port_Number'])),str(int(x['link_partner_port_num']))) \
                                                                            , axis=1)
    return join_iteration   

def save_results_in_sheet (df, sheet_name,writer):

    if isinstance(df,pd.DataFrame) == False:
        return

    if df.shape[0]==0:
        print ('No data for ',sheet_name, 'sheet')

        # --- don't save data if there is no results
        # df_msg = pd.DataFrame(["No results"], columns = ['msg'])
        # df_msg.to_excel(writer, sheet_name=sheet_name)

    else:
        df.to_excel(writer, sheet_name=sheet_name, index = False)
