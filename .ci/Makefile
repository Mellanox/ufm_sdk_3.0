
jjb-blsm:
	# IMPORTANT: configure the /etc/jenkins_jobs/jenkins_jobs.ini file to point to the relevant blossom
	python3 -m jenkins_jobs --conf /etc/jenkins_jobs/jenkins_jobs.ini update $(shell pwd)/pipeline/proj_jjb_nbuprod.yaml

jjb-blsm-test:
	# IMPORTANT: configure the /etc/jenkins_jobs/jenkins_jobs.ini file to point to the relevant blossom
	python3 -m jenkins_jobs --conf /etc/jenkins_jobs/jenkins_jobs.ini test $(shell pwd)/pipeline/proj_jjb_nbuprod.yaml
