API Streaming
--------------------------------------------------------

this script allows streaming UFM APIs to fluentd endpoint

Prerequisites 
--------------------------------------------------------

To install all prerequisites, please run :

`pip install -r requirements.txt` 


Configuration
-------------------------------------------------------- 
Please copy api-streaming.sample.cfg and rename it to api-streaming.cfg, and set the Fluentd and UFM parameters.

Run  
-------------------------------------------------------- 
python api-streaming.py

Use  
-------------------------------------------------------- 
This application is not a daemon; you should run it via time-based job scheduler (cron job).
