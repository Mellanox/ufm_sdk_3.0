#!/bin/bash
# Copyright (C) Mellanox Technologies Ltd. 2001-2021.   ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Mellanox Technologies Ltd.
# (the "Company") and all right, title, and interest in and to the software product,
# including all associated intellectual property rights, are and shall
# remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

# ================================================================
# This script prepares and installs specific openssl version (1.0.2k)
# This version of the OpenSSL is a dependency for /opt/ufm/telemetry/collectx/lib/libraw_msgpack_api.so
# ================================================================


# Download and extract OpenSSL
wget https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz -O openssl.tar.gz
tar -zxf openssl.tar.gz
pushd openssl-1.0.2k

# Configure OpenSSL with a specific prefix
./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl shared

# Compile and install
make clean
make
make test
make install

# Update the dynamic linker cache
ldconfig

ln -s /usr/local/ssl/lib/libssl.so.1.0.0 /usr/lib/x86_64-linux-gnu/libssl.so.10
ln -s /usr/local/ssl/lib/libcrypto.so.1.0.0 /usr/lib/x86_64-linux-gnu/libcrypto.so.10
ldconfig

popd

rm -rf openssl-1.0.2k openssl.tar.gzl

exit 0
