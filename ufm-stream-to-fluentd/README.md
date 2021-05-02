UFM stream To FluentD endpoint
--------------------------------------------------------


This plugin is used to reflect topology changes with time provided by UFM towered FluentD endpoint.


Prerequisites 
--------------------------------------------------------

To install all prerequisites, please run :

    pip install -r requirements.txt

Run  
-------------------------------------------------------- 
### 1) using command line arguments :


    python ufm-stream-to-fluentd.py --fluentd_host=fluentd_host --fluentd_port=fluentd_port --ufm_host=ufm_host --ufm_username=ufm_username --ufm_protocol=https --ufm_password=ufm_password


### 2) using configuration file:
  
  - copy config file sample ufm-stream-to-fluentd.sample.cfg to ufm-stream-to-fluentd.cfg 
      
    
    cp ufm-stream-to-fluentd.sample.cfg ufm-stream-to-fluentd.cfg

  - Edit config file with relevant parameters 

    
    vi ufm-stream-to-fluentd.cfg

  - Run

    
    python ufm-stream-to-fluentd.py

 
   

Use
-------------------------------------------------------- 
This application is not a daemon; you should run it via time-based job scheduler (cron job).
