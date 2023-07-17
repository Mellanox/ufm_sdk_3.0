UFM-SLURM Integration
--------------------------------------------------------


UFM is a powerful platform for managing scale-out computing environments. UFM enables data center operators to monitor, efficiently provision, and operate the modern data center fabric.
Using UFM with SLURM offer a good solution to track network bandwidth, congestion, errors and resource utilization of compute nodes of SLURM jobs.



Prerequisites
--------------------------------------------------------


UFM 6.10 installed on a RH7x machine with sharp_enabled & enable_sharp_allocation true and running in management mode.
python 2.7 on SLURM controller.
UFM-SLURM Integration tar file.
Generate token_auth


Installing
--------------------------------------------------------


### 1) Using SLURM controller, extract UFM-SLURM Integration tar file:
	   tar -xf ufm_slurm_integration.tar.gz

### 2) Run the installation script.
	   sudo ./install.sh



Generate token_auth
--------------------------------------------------------


If you set auth_type=token_auth in UFM SLURM’s config file, you must generate a new token by logging into the UFM server and running the following curl command:

curl -H "X-Remote-User:admin" -XPOST http://127.0.0.1:8000/app/tokens

Then you must copy the generated token and paste it into the config file beside the token parameter.



Deployment
--------------------------------------------------------


After installation, the configurations should be set and UFM machine should be running.
Several configurable settings need to be set to make the integration run.

### 1) On SLURM controller open /etc/slurm/ufm_slurm.conf
       sudo vim /etc/slurm/ufm_slurm.conf

### 2) Set the following keys, then save the file:
	   ufm_server:       UFM server IP address to connect to
 	   ufm_server_user:  Username of UFM server used to connect to UFM if you set 
                             auth_type=basic_auth.
	   ufm_server_pass:  UFM server user password.
	   partially_alloc:  Whether to allow or not allow partial allocation of nodes
	   pkey:             By default it will by default management Pkey 0x7fff
	   auth_type:        One of (token_auth, basic_auth) by default it token_auth
	   token:            If you set auth_type to be token_auth you need to set 
                             generated token. Please see Generate token_auth section.
	   log_file_name:    The name of integration logging file

### 3) Run UFM in 'Management' mode.
	 - On UFM machine, open the ufm config file /opt/ufm/files/conf/gv.cfg
	 - In section [Server], set the key: "monitoring_mode" to no and then save the file.
	   monitoring_mode=no
	 - Start UFM
		* HA mode: /etc/init.d/ufmha start
		* SA mode: /etc/init.d/ufmd start



Running
--------------------------------------------------------


After installation and deployment of UFM-SLURM integration, the integration should work for every submitted SLURM job automatically.

    - Using the Slurm controller submit a new SLURM job.
	  for example: # sbatch -N2 batch1.sh
    - In UFM side, a new SHArP reservation will be created based on job_id,
      job nodes and set pkey in ufm_slurm.conf file.
    - A new pkey will be created contains all the ports of job nodes to
      allow the SHArP nodes to be communicated on top of it.
    - After the SLURM job is completed, UFM deletes the created SHArP 
      reservation and pkey.
    - From the time that a job is submitted by SLURM server until 
      completion, a log file called /tmp/ufm_slurm.log logs all the 
      actions and errors occurs during the execution. This log file 
      could be changed by modify log_file_name parameter in UFM_SLURM
      config file /etc/slurm/ufm_slurm.conf.
