# UFM LOGANALYZER

**Warning:** This feature is still under development and right now should only be used internally

## What
This tool should help developers find issues in a UFM sysdump or logs.

It is meant to help find issues fast ,without the need to manually go over logs.

## How to use
The tool is meant to run from a PC or a remote connection

### Prerequisites
Install the needed Python dependencies
```
python3 -m pip install -r src/loganalyze/requirements.txt
```
Install software for PDF creation:
```
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libjpeg-dev zlib1g-dev

# For Red Hat/CentOS/Fedora
sudo yum install -y libjpeg-devel zlib-devel
```
Know your UFM sysdump location.

####  Running on a remote server
Since the tool generates graphs, you will need to setup an X11 forwarding:

1. Mac - Install and run [Quartz](https://www.xquartz.org/). Windows - Install and run [Xming](http://www.straightrunning.com)
2. On your remote server (Ubuntu/RedHat), make sure the x11 forwarding is enabled: 
``` 
vim /etc/ssh/sshd_config
#Enalbe x11
X11Forwarding yes
```
3. Restart the ssh service `systemctl restart ssh` or `systemctl restart sshd` depends on the OS.
4. Install `python3-tk` using `sudo yum install python3-tkinter` or `sudo apt-get install python3-tk` depends on the OS.
5. When you SSH to the server, use the flag `-X`, for example `ssh -X root@my-vm`

If you would like to make sure it is working, once connection is done, do `xclock &`. This should start a clock on your machine.

### How to run
```
./log_analzer.sh  [options] -l <path to dump>
```

While the options are:
```
options:
  -h, --help            show this help message and exit
  -l LOCATION, --location LOCATION
                        Location of dump tar file.
  -d DESTINATION, --destination DESTINATION
                        Where should be place the extracted logs and the CSV files.
  --extract-level EXTRACT_LEVEL
                        Depth of logs tar extraction, default is 1
  --hours HOURS         How many hours to process from last logs. Default is 6 hours
  -i, --interactive     Should an interactive Ipython session start. Default is False
  -s, --show-output     Should the output charts be presented. Default is False
  --skip-tar-extract    If the location is to an existing extracted tar or just UFM logs directory, skip the tar extraction and only copy the needed logs. Default is False
  --interval [{1min,10min,1h,24h}]
                        Time interval for the graphs. Choices are: '1min'- Every minute, '10min'- Every ten minutes, '1h'- Every one hour, '24h'- Every 24 hours. Default is '1H'.
  ```

What is mandatory:
1. `--location`.

## Which files are taken from the dump
The following list: `event.log, ufmhealth.log, ufm.log, ibdiagnet2.log, console.log, rest_api.log and second telemetry samples`

Also, each log `tar` is taken, according to the `extract-level` flag.
## How it works
1. Given the list of logs to work with, they are extract from the dump to the destination directory.
2. Each log is being parsed, with his own unique set of regex's.
3. Each parsed line is saved in a CSV file that represents the parsed line from the specific log.
4. Once all logs are parsed, we use Pandas analyzer to load the CSV's and query them.
5. A pre defined set of analysis runs and outputs some plots and data to the terminal.
6. A PDF file is created with the summary of the images and the fabric size.
7. We are starting an interactive Python session, where the user can run pre-defined analysis function on the parsed data, or do personal data query/manipulation to find the needed data

## Link flapping
This logic uses second telemetry counters to identify if links are flapping due to real issues.
The input is the telemetry sample from last week and last 5 minutes.
Output is a list of links to check.
This logic will show links that:
1. Both sides of the link went down together.
2. Thermal shut down.
3. If one side went down and the other side was not rebooted.


![Tool flow](img/loganalzer.png)


