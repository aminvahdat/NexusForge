#!/bin/bash
echo "local all all trust" > /var/lib/postgresql/data/pg_hba.conf.tmp
cat /var/lib/postgresql/data/pg_hba.conf >> /var/lib/postgresql/data/pg_hba.conf.tmp
cp /var/lib/postgresql/data/pg_hba.conf.tmp /var/lib/postgresql/data/pg_hba.conf
sed -i 's/scram-sha-256/trust/' /var/lib/postgresql/data/pg_hba.conf
echo "Fixed pg_hba.conf"
