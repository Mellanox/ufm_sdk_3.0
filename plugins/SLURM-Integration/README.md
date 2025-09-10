UFM-SLURM Integration
--------------------------------------------------------


UFM is a powerful platform for managing scale-out computing environments. UFM enables data center operators to monitor, efficiently provision, and operate the modern data center fabric.
Using UFM with SLURM offer a good solution to track network bandwidth, congestion, errors and resource utilization of compute nodes of SLURM jobs.



Prerequisites
--------------------------------------------------------


UFM version installed and running on one of the nodes connected to the SLURM controller over TCP.
Python 3 installed on the SLURM controller.
Latest version of the UFM-SLURM Integration.


Installing
--------------------------------------------------------


### 1) Using SLURM controller, extract the UFM-SLURM Integration tar file:
	   tar -xf ufm_slurm_integration.tar.gz

### 2) Run the installation script.
	   sudo ./install.sh
	   or run the ./install.sh with root permissions



Generate token_auth
--------------------------------------------------------


If you set auth_type=token_auth in UFM SLURM’s config file, you must generate a new token by logging into the UFM server and running the following curl command:

curl -H "X-Remote-User:admin" -XPOST http://127.0.0.1:8000/app/tokens

Then you must copy the generated token and paste it into the UFM SLURM’s config file beside the token parameter.



Configure the SLURM server for Kerberos authentication
-------------------------------------------------------


### 1) Verify that both the UFM server and the Kerberos server are appropriately configured to support Kerberos authentication.
### 2) Install Required Packages: Execute the command yum install krb5-libs krb5-workstation to install the necessary packages.
### 3) Adjust the /etc/krb5.conf file to match your realm, domain, and other settings, either manually or by copying it from the Kerberos server.
### 4) Obtain a Kerberos ticket-granting ticket (TGT) using one of the following methods:
        Using the keytab file:
            Copy the Keytab from Kerberos server to SLURM server Machine.
            Create the Kerberos ticket by running: kinit -k -t /path/to/your-keytab-file HTTP/YOUR-HOST-NAME@YOUR-REALM

        Using user principle:
            In the Kerberos server create user principle by running: kadmin.local addprinc user_name
            In the SLURM client, acquire the TGT by running: kinit user_name
### 5) Test Kerberos Authentication
        Use curl to verify the user's ability to authenticate to UFM REST APIs using Kerberos authentication:
        curl --negotiate -i -u : -k 'https://<ufm_server_name>/ufmRestKrb/app/tokens'
### 6) Configure ufm_slurm.conf file on the SLURM server:.
        Set ufm_server=<ufm_host_name>, recommended to use the host name and not host IP.
        Set auth_type=kerberos_auth.
        Set principal_name=<your_principal_name>; retrieve it using the klist command.


Deployment
--------------------------------------------------------


After installation, the configurations should be set, and the UFM machine should be running. Several configurable
settings need to be adjusted to make the UFM-SLURM Integration function properly.

### 1) On the SLURM controller open /etc/slurm/ufm_slurm.conf
       sudo vim /etc/slurm/ufm_slurm.conf

### 2) Set the following keys, then save the file:
	   ufm_server:            UFM server IP address to connect to
 	   ufm_server_user:       Username of UFM server used to connect to UFM if you set auth_type=basic_auth.
	   ufm_server_pass:       UFM server user password.
       pkey_allocation:       When set to true, UFM–SLURM Integration will allocate a PKEY for the SLURM job. Otherwise, it will use the default management PKEY: 0x7fff.
       pkey_allocation_mode:  PKEY allocation mode: one of {static, dynamic}.
                              - static  : use a statically assigned PKEY when creating a new PKEY.
                              - dynamic : use dynamic assignment when creating a new PKEY based of the slurm-job-id.
	   pkey:                  Used only when pkey_allocation_mode=static. If not set, the default management PKEY (0x7fff) will be used.
	   partially_alloc:       Whether to allow or not allow partial allocation of nodes
       auth_type:             One of (token_auth, basic_auth, kerberos_auth) by default it token_auth
	   token:                 If you set auth_type to be token_auth you need to set generated token. Please see Generate token_auth section.
       principal_nam:         principal name to be used in kerberos authentication when you set auth_type to be kerberos_auth.
	   log_file_name:         The path of the UFM-SLURM integration logging file

### 3) Run UFM in 'Management' mode.
	 - On UFM machine, open the ufm config file /opt/ufm/files/conf/gv.cfg
	 - In section [Server], set the key: "monitoring_mode" to no and then save the file.
	   monitoring_mode=no
	 - Start UFM
		* HA mode: ufm_ha_cluster start
		* SA mode: systemctl start ufm-enterprise



Running
--------------------------------------------------------


After the installation and deployment of UFM-SLURM Integration, the integration should automatically handle every submitted SLURM job.

    - Use the SLURM controller to submit a new SLURM job, for example: sbatch -N2 batch1.sh.
    - On the UFM side, a new SHArP reservation will be created based on the job ID and the job nodes if the
      sharp_allocation parameter in the ufm_slurm.conf file is set to true.
    - A new pkey containing all the ports of the job nodes will be created to allow the SHArP nodes to communicate on top of it.
    - After the SLURM job is completed, UFM deletes the created SHArP reservation and pkey.
    - From the time a job is submitted by the SLURM server until its completion, a log file called /var/log/slurm/ufm_slurm.log
      records all actions and errors that occur during execution. This log file location can be changed by modifying the
      log_file_name parameter in the UFM_SLURM configuration file located at /etc/slurm/ufm_slurm.conf.
