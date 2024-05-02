UFM batch isolate devices
--------------------------------------------------------


This plugin is used to isloate all ports but 1, for a given list of switches


Prerequisites
--------------------------------------------------------

To install all prerequisites, please run :

    pip3 install -r requirements.txt

Input file
--------------------------------------------------------
The input file should be a valid CSV
Each row should be a pair of <switch GUID, Port>

In order to identify a batch, add a line with `===,`

Run
--------------------------------------------------------
###  To run the script for a given host:

    python3 batch_isolate_devices.py -f <path to CSV file> -h <host>


 Running syntax
--------------------------------------------------------

| Option                     | Description                                            |
|----------------------------|--------------------------------------------------------|
| -h, --help                 | Show help message and exit                             |
| -H HOST, --host HOST       | UFM host address                                       |
| -u USER, --user USER       | UFM user name                                          |
| -p PASSWORD, --password PASSWORD | UFM password                                       |
| --num_retries NUM_RETRIES  | Number of retries when marking Switch as isolated      |
| --sleep_time SLEEP_TIME    | Time to sleep until checking the isolation job status  |
| -f FILE, --file FILE       | Path to CSV file 
