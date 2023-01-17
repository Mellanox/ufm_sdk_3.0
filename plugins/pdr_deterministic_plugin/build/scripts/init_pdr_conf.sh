#!/bin/bash

ufm_dir=/opt/ufm
conf_dir=$ufm_dir/files/conf
ufm_conf=$conf_dir/gv.cfg
secodary_telemtry_defaults=$conf_dir/secondary_telemetry_defaults
secodary_defaults_launch=$secodary_telemtry_defaults/launch_ibdiagnet_config.ini
secodary_telemtry_conf=$conf_dir/secondary_telemetry
default_cset=$secodary_telemtry_defaults/prometheus_configs/cset/enterprise_low_freq.cset
running_cset=$secodary_telemtry_conf/prometheus_configs/cset/enterprise_low_freq.cset
fset_dir=$secodary_telemtry_conf/prometheus_configs/fset
ufmd_location=/etc/init.d/ufmd

mkdir -p $fset_dir
printf "[CableInfo]\n^cable_temperature" > $fset_dir/low_freq.fset
printf "\nsymbol_ber_f=^symbol_ber$" >> $default_cset
printf "\n^fec_mode_active$" >> $default_cset
printf "\nsymbol_ber_f=^symbol_ber$" >> $running_cset
printf "\n^fec_mode_active$" >> $running_cset

# enabling active FEC mode collect in secondary instance
sed -i 's/.*arg17=.*/arg_17=--get_phy_info --enabled_reg DD_PDDR_OP/g' $secodary_defaults_launch
# enbale cable data collection
sed -i 's/plugin_env_CLX_EXPORT_API_DISABLE_CABLEINFO=1/plugin_env_CLX_EXPORT_API_DISABLE_CABLEINFO=0/g' $secodary_defaults_launch
sed -i 's/#plugin_env_PROMETHEUS_FSET_DIR=.*/plugin_env_PROMETHEUS_FSET_DIR=/g' $secodary_defaults_launch
sed -i 's/plugin_env_CLX_EXPORT_API_SKIP_PHY_STAT=.*/plugin_env_CLX_EXPORT_API_SKIP_PHY_STAT=0/g' $secodary_defaults_launch

sed -i 's/secondary_telemetry=.*/secondary_telemetry=true/g' $ufm_conf
sed -i 's/additional_cset_urls=.*/additional_cset_urls=http:\/\/127.0.0.1:9002\/csv\/fset\/low_freq/g' $ufm_conf
sed -i 's/high_ber_ports_auto_isolation.*/high_ber_ports_auto_isolation=false/g' $ufm_conf

$ufmd_location ufm_telemetry_restart
sleep 2
$ufmd_location model_restart
sleep 2
echo "finished initialize pdr configuration"