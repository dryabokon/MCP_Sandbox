#!/bin/bash
#---------------------------------------------------------------------------------------------------------------------
DB_USER="root"
DB_PASS="YourStrong!Passw0rd"
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="imdb"
#---------------------------------------------------------------------------------------------------------------------
conn_str="mysql+pymysql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
#conn_str="mysql+pymysql://root:YourStrong!Passw0rd@localhost:3306/imdb"
echo $conn_str
#---------------------------------------------------------------------------------------------------------------------
SQL="SELECT count(*) from title_ratings"
mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" --protocol=TCP "${DB_NAME}" -e "${SQL}"