# Welcome To UFM Performance POC

## Before Running
you need the following dependencies to be in your setup
#### install flask by running 
> pip3 install flask
#### install flask_restful by running 
> pip3 install flask_restful

#### install apscheduler by running
> pip3 install apscheduler

## Running
> flask run

## Configure Apache as reverse proxy
###### Edit & copy the file ufm-rest-plugin.conf to /etc/httpd/conf.d
###### restart apache
> service httpd restart
###### Now your project is running under apache based on the path mentioned in ufm-perf-poc.conf
