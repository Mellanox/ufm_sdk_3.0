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

external_endpoint_port=$1
internal_endpoint_port=$2

# configure the apache to work on external_endpoint_port instead of 80
sed -i "0,/Listen [0-9]*/{s/Listen [0-9]*/Listen $external_endpoint_port/}" /etc/apache2/ports.conf
# adding the reverse proxy configurations for the endpoint server
# endpoint server works internally on port internal_endpoint_port
touch /etc/apache2/conf-available/grafana-plugin.conf
cat > /etc/apache2/conf-available/grafana-plugin.conf << EOL
<Location /labels>
    ProxyPass http://127.0.0.1:${internal_endpoint_port} retry=1 Keepalive=On
    ProxyPassReverse http://127.0.0.1:${internal_endpoint_port}
</Location>
EOL
ln -s /etc/apache2/conf-available/grafana-plugin.conf /etc/apache2/conf-enabled/grafana-plugin.conf
a2enmod proxy_http
systemctl restart apache2

exit 0
