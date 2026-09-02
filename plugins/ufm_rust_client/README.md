## *UFM rust client*
The rust client of UFM

### *Build*
To install [rust](https://www.rust-lang.org/tools/install) on the machine.

```
cargo build
```

### *Usage*

Use the following syntax to run `ufmcli` commands from your terminal window:
```
ufmcli [flags] [command] [parameters]
```

where flags, command, and parameters are:
* `flags`: Specifies optional flags. For example, you can use the `--ufm-address` or `--ufm-token` flags to specify the address and token of the UFM server.
* `command`: Specifies the operation that you want to perform on UFM, for example `view`, `list`, `delete`, `create`.
* `parameters`: Specifies the parameters for command, for example `-p` or `--pkey` to specify the pkey for the partition.

`ufmcli` needs to know the UFM server address and authentication(username/password or token) to access UFM server. 

There are two ways to set the UFM server address and authentication for `ufmcli` command.
* Environment: Set environment `UFM_ADDRESS` for the UFM server address, for example `export UFM_ADDRESS=http://hpc-cloud-gw.mtr.labs.mlnx:4402`. Set environment `UFM_TOKEN` or `UFM_USERNAME`, `UFM_PASSWORD` for the authentication.
* Flag: Specifies the flags in the `ufmcli` command, you can use `--ufm-address` to specify the UFM address and `--ufm-token` or `--ufm-username`, `--ufm-password` to specify the authentication.


#### *Version*
```
./ufmcli version
6.11.1-2
```
#### *Create a Partition Key*
```
./ufmcli create --pkey 5 --mtu 2 --membership full --service-level 0 --rate-limit 2.5 --guids 0011223344560200 --guids 1070fd0300176625 --guids 0011223344560201
```

#### *View a Partition Key*
```
./ufmcli view --pkey 0x5
Name           : api_pkey_0x5
Pkey           : 0x5
IPoIB          : false
MTU            : 2
Rate Limit     : 2.5
Service Level  : 0
Ports          : 
    GUID                ParentGUID          PortType  SystemID            LID       SystemName     LogState  Name                
    0011223344560200    1070fd0300176624    virtual   1070fd0300176624    7         hpc-cloud01    Active                        
    1070fd0300176625                        physical  1070fd0300176624    4         hpc-cloud01    Active    1070fd0300176625_2  
    0011223344560201                                                      65535                    Unknown  

```

#### *List Partition Keys*
```
./ufmcli list
Name           Pkey      IPoIB     MTU       Rate      Level     
api_pkey_0x5   0x5       false     2         2.5       0         
api_pkey_0x2   0x2       false     2         2.5       0         
management     0x7fff    true      2         2.5       0         
api_pkey_0x1   0x1       false     2         2.5       0         
api_pkey_0x4   0x4       false     2         2.5       0  
```

#### *Delete a Partition Key*
```
./ufmcli delete --pkey 0x2
```