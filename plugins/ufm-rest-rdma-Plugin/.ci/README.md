
# UFM_REST_RDMA CI/CD

## Update Jenkins if proj_jjb.yaml was changed

```
  cd .ci
  make jjb
```

## Retrigger CI

Put a comment with "bot:retest"

## Sanity test for rest-rdma plugin

Installing container on client and server
sending POST requests, Delete Request, Get Request and Post ibidiagnt request:(for example)
--ufm_rdma.py -r client -t simple -a POST -w ufmRest/actions/add_guids_to_pkey -l'{"pkey": "0x0002","guids":["f452140300188540"],"index0": true,"default_membership": "full","ip_over_ib": false}' 
--ufm_rdma.py -r client -t simple -a POST -w ufmRest/actions/remove_guids_from_pkey -l '{"pkey":"0x0002","guids":["f452140300188540"]}' 
--ufm_rdma.py -r client -t simple -a GET -w ufmRest/actions/get_all_pkeys?guids_data=true  
--ufm_rdma.py -r client -t ibdiagnet -a POST -w ufmRest/reports/ibdiagnetPeriodic -l '{"general": {"name": "kol", "location": "local", "running_mode": "once"}, "command_flags": {"--pc": ""}}' 




## CI/CD 

This CD/CD  pipeline based on ci-demo. All information can be found in main ci-demo repository.

[Read more](https://github.com/Mellanox/ci-demo/blob/master/README.md)

