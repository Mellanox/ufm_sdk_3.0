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



import argparse
from datetime import datetime
import json
import traceback
from openpyxl import Workbook
import pandas as pd


from utils import FileSource, \
    read_and_preprocessing_file, \
    add_partner_info 
from utils import add_link_hash_id, save_results_in_sheet

def create_workbook(path):
    workbook = Workbook()
    workbook.save(path) 
    writer = pd.ExcelWriter(path, engine = 'xlsxwriter')
    return writer

def fill_missing_partner(df1, df2):

  
    df2['link_partner_node_guid'] = df2['link_partner_node_guid'].replace('0x0000000000000000', '')
    df2['link_partner_port_num'] = df2['link_partner_port_num'].replace('0x0000000000000000', '')
    df2['link_partner_port_num'] = df2['link_partner_port_num'].replace('0', 0)
    df2['link_partner_port_num'] = df2['link_partner_port_num'].replace('', 0)
    df2['link_partner_port_num'] = df2['link_partner_port_num'].replace(0.0, 0)

    df_join = pd.merge(left = df2, right  = df1[["Node_GUID", "Port_Number",'link_partner_node_guid','link_partner_port_num']], how = 'left', on = ["Node_GUID", "Port_Number"])

    df_join = df_join.rename(columns  = {'link_partner_node_guid_x':'link_partner_node_guid', 'link_partner_port_num_x':'link_partner_port_num'})

    df_join['link_partner_node_guid'] = df_join['link_partner_node_guid'].replace('', pd.NA).fillna(df_join['link_partner_node_guid_y']).replace(pd.NA,'')
    df_join['link_partner_port_num'] = df_join['link_partner_port_num'].replace(0, pd.NA).fillna(df_join['link_partner_port_num_y']).replace(pd.NA,0)


    df_join = df_join.drop(columns = ['link_partner_node_guid_y','link_partner_port_num_y'])

    return df_join

def run_analysis(filename1,filename2,raw_ber_th,Effective_ber_th,symbol_ber_threshold,
                  leaf_str, spine_str, core_spine,hca_str_list ,use_all_columns_flag, writer, file_type,ignore_server_list=[]
                  ):



        df1 = read_and_preprocessing_file(filename1, leaf_str,spine_str,core_spine,hca_str_list)
        df2 = read_and_preprocessing_file(filename2, leaf_str,spine_str,core_spine,hca_str_list)
        
        # complete missing partner in df2 based on df1
        df2 = fill_missing_partner(df1, df2)
        df1_with_partner = add_partner_info(df1,use_all_columns_flag,ignore_server_list=ignore_server_list)
        df2_with_partner = add_partner_info(df2,use_all_columns_flag,ignore_server_list=ignore_server_list)

        #linkdown both sides
        linkdown_df1,linkdown_summary_dict = get_suspected_real_linkdown (df1_with_partner, df2_with_partner,min_to_filter_reboot_threshold=10,dispaly_all_col_flag=use_all_columns_flag)

        save_results_in_sheet(linkdown_df1, 'Suspected real linkdown',writer)


def run_analysis_and_report(p_config_file,report_file, filename1,filename2):
    print('start run_analysis_and_report',filename1,filename2 )
    writer = None
    try:
            #load config - todo move to input
        with open(p_config_file) as config_file:
            data = json.load(config_file)
            
            leaf_str = data ['leaf_str']
            spine_str = data ['spine_str']
            core_spine = data['core_spine']
            hca_str_list = data ['hca_str_list']
            raw_ber_th = data['raw_ber_th']
            Effective_ber_th = data['Effective_ber_th']
            symbol_ber_threshold = data['symbol_ber_threshold']
            use_all_columns_flag = data['use_all_columns_flag']
            file_type_str = data ['file_type']
            if file_type_str == 'UFM':
                file_type = FileSource.UFM
            elif file_type_str=='COLLECTX':
                file_type = FileSource.collectx
            
            ignore_server_list = data.get('ignore_server_list',[])

            
            writer = create_workbook(report_file) 

          
            run_analysis(filename1,filename2,raw_ber_th,Effective_ber_th,symbol_ber_threshold,
                        leaf_str, spine_str, core_spine,hca_str_list,
                        use_all_columns_flag,writer, file_type,ignore_server_list=ignore_server_list)
            
            print('End Phy layer files analysis')
            print('Final report:',report_file)

    except Exception as e: 
        print(e)
        traceback.print_exc()
    finally :
        if writer:
            writer.close()



def get_suspected_real_linkdown(df1_with_partner, df2_with_partner,min_to_filter_reboot_threshold = 10, dispaly_all_col_flag = False): 

    func_summary_dict = dict()
    col4diff_calc = ['Effective_Errors','Symbol_Errors','PortRcvDataExtended','Link_Down',\
                    'Link_Down_partner']
    
    if dispaly_all_col_flag:
        col2_present = df1_with_partner.columns
        
    else:
        # relevant column to present
        col2_present = ['timestamp','timestamp_partner','Node_GUID','Device_ID','node_description',\
                        'Port_Number','Device_ID_partner',\
                    'link_partner_description','link_partner_node_guid','link_partner_port_num',\
                        'Cable_SN','Time_since_last_clear','Time_since_last_clear_partner','Total_Raw_BER', 
                        'Effective_BER','Symbol_BER',
                        'Total_Raw_BER_partner', 'Effective_BER_partner','Symbol_BER_partner',               
                    'max_time_since_clear_by_switch_or_server','max_time_since_clear_by_switch_or_server_partner',
                    'Status_Message','local_reason_opcode',	'remote_reason_opcode',
                    'Status_Message_partner','local_reason_opcode_partner',	'remote_reason_opcode_partner','estimated_time','estimated_time_partner','time_to_link_up_msec','time_to_link_up_msec_partner']+col4diff_calc
        
    
    # take common columns
    col2_present1 = [col for col in col2_present if col in df1_with_partner.columns]
    col2_present1 = [col for col in col2_present1 if col in df2_with_partner.columns]


        # join df1 with df2
    join_iteration = pd.merge(df1_with_partner[col2_present1], df2_with_partner[col2_present1] ,how='inner', 
                            left_on=['Node_GUID','Port_Number','link_partner_description','link_partner_node_guid','link_partner_port_num'],
                            right_on=['Node_GUID','Port_Number','link_partner_description','link_partner_node_guid','link_partner_port_num']
                            )
    # calcualate diff columns
    for col in col4diff_calc:
        join_iteration['diff_'+col] = join_iteration[col+'_y'] - join_iteration[col+'_x']


    # take the latest data to present
    col_y = [col+'_y' for col in col2_present1]
    col_latest = [col for col in col2_present1]

    col_naming_dict = {}
    col_naming_dict = dict(zip(col_y, col_latest))

    join_iteration = join_iteration.rename(columns = col_naming_dict, errors='ignore')
    
    
    join_iteration = join_iteration.rename (columns = {'timestamp_x':'prev_timestamp',
                                                       'Link_Down_x':'prev_Link_Down',
                                                       'Link_Down_partner_x':'prev_Link_Down_partner',
                                                       'Time_since_last_clear_x': 'prev_Time_since_last_clear',
                                                       'Time_since_last_clear_partner_x': 'prev_Time_since_last_clear_partner'}, errors='ignore')
    
    
    # add link id hash  
    # join_iteration ['link_hash_id']  = join_iteration.apply(lambda x: hash(min(x['Node_GUID'],x['link_partner_node_guid']) + \
    #                                                                        max(x['Node_GUID'],x['link_partner_node_guid']) + \
    #                                                                         min(str(int(x['Port_Number'])),str(int(x['link_partner_port_num'])))+\
    #                                                                          max(str(int(x['Port_Number'])),str(int(x['link_partner_port_num']))) \
    #                                                                             ), axis=1)
    # add link id hash  as concat


    
    join_iteration = add_link_hash_id(join_iteration)


    join_iteration1 = join_iteration

    # remove old link down by estimated time
    # join_iteration1 ['estimated_time'] = join_iteration1['timestamp'] - 60*join_iteration1['Time_since_last_clear'] -- moved it to the preprocessing
    join_iteration1 = join_iteration1[join_iteration1.estimated_time>join_iteration1.prev_timestamp]

    join_iteration1['estimated_time'] = join_iteration1['estimated_time'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S')) 


    # add support of linkdown_diff<0 but linkdown value is >0
    df_linkdown = join_iteration1[((abs(join_iteration1.Time_since_last_clear - join_iteration1.Time_since_last_clear_partner)<10) & ((join_iteration1.diff_Link_Down>0) | ((join_iteration1.diff_Link_Down<0) & (join_iteration1.Link_Down>0))) & ((join_iteration1.diff_Link_Down_partner>0) | ((join_iteration1.diff_Link_Down_partner<0) & (join_iteration1.Link_Down_partner>0)))) | \
                                  ((join_iteration1.diff_Link_Down>0) & (abs(join_iteration1.Time_since_last_clear_partner- join_iteration1.max_time_since_clear_by_switch_or_server_partner)>min_to_filter_reboot_threshold)) | \
                                  ((join_iteration1.local_reason_opcode==25) | (join_iteration1.remote_reason_opcode==25) )
                                  ]    



    if ('Device_ID' in df_linkdown.columns) & ('Device_ID_partner' in df_linkdown.columns):
        # todo - for ethernet , need to use hostname convetion
        df_linkdown['link_type'] = 'other'
        mask = (df_linkdown.Device_ID.str.contains('Connect')) & (df_linkdown.Device_ID_partner.str.contains('Quantum'))
        df_linkdown.loc[mask,'link_type'] = 'switch-hca'

        mask = (df_linkdown.Device_ID.str.contains('Quantum')) & (df_linkdown.Device_ID_partner.str.contains('Connect'))
        df_linkdown.loc[mask,'link_type'] = 'switch-hca'

        mask = (df_linkdown.Device_ID.str.contains('Quantum')) & (df_linkdown.Device_ID_partner.str.contains('Quantum'))
        df_linkdown.loc[mask,'link_type'] = 'switch-switch'

 

    # use /2 because table have duplication A->B + B->A
    # func_summary_dict['Number of links - diff linkdown>0'] = np.floor(join_iteration1[join_iteration1.diff_Link_Down>0].shape[0]/2)
    # func_summary_dict['Number of links - suspected linkdown'] = np.floor(df_linkdown.shape[0]/2)
        # 2407 - change to count unique link id
    func_summary_dict['Number of links - suspected linkdown switch-switch'] = df_linkdown[df_linkdown['link_type'] == 'switch-switch'].link_hash_id.drop_duplicates().shape[0]
    func_summary_dict['Number of links - suspected linkdown switch-hca'] = df_linkdown[df_linkdown['link_type'] == 'switch-hca'].link_hash_id.drop_duplicates().shape[0]
   
    number_active_links = df2_with_partner[df2_with_partner.Phy_Manager_State == 'Active'].shape[0]
    number_link_down  = df_linkdown.shape[0]
    func_summary_dict ['pct of link down'] = round( 100* number_link_down/number_active_links,2)


        # set_df_col_order 
    col_order =  ['link_hash_id','link_type']+list(df2_with_partner.columns) + ['diff_Link_Down', 'diff_Link_Down_partner', 'prev_Link_Down', 'prev_Link_Down_partner', \
                                                                                'prev_Time_since_last_clear', 'prev_Time_since_last_clear_partner',\
                                                                                'estimated_time']
    
    col_order1 = [col for col in col_order if col in df_linkdown.columns]
    df_linkdown = df_linkdown[col_order1]
    

    return df_linkdown, func_summary_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='The codr analyze 2 collectx/UFM file - one iteration in every file')
    parser.add_argument('-f1','--earlier_file', help='Earlier file name path', required=True)
    parser.add_argument('-f2','--latest_file', help='Latest file name path', required=True)
    parser.add_argument('-c','--config', help='config file', required=True)
    parser.add_argument('-r','--report_file', help='output report file', required=True)
    args = vars(parser.parse_args())

    filename1 = args['earlier_file'] 
    filename2 = args['latest_file'] 
    config_file = args['config']
    report_file =args['report_file']

    # moved all logic to a function
    run_analysis_and_report(config_file,report_file, filename1,filename2)
