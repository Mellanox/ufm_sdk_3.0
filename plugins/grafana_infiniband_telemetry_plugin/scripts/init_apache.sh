#!/bin/bash
# Copyright (C) Mellanox Technologies Ltd. 2001-2022.   ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Mellanox Technologies Ltd.
# (the "Company") and all right, title, and interest in and to the software product,
# including all associated intellectual property rights, are and shall
# remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.


set -eE

# configure the apache to work on 8982 instead of 80
sed -i 's/80/8982/' /etc/apache2/ports.conf
# adding the reverse proxy configurations for the endpoint server
# endpoint server works internally on port 8984
touch /etc/apache2/conf-available/grafana-plugin.conf
cat > /etc/apache2/conf-available/grafana-plugin.conf << EOL
<Location /labels>
    ProxyPass http://127.0.0.1:8984 retry=1 Keepalive=On
    ProxyPassReverse http://127.0.0.1:8984
</Location>
EOL
ln -s /etc/apache2/conf-available/grafana-plugin.conf /etc/apache2/conf-enabled/grafana-plugin.conf
a2enmod proxy_http
systemctl restart apache2

exit 0
