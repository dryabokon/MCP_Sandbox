#!/bin/bash
set -e

CONTAINER=sql2019
SA_PASSWORD='Pass@word123'
PORT=1433

echo "==== 1. Start/Create SQL Server container ===="

if [ "$(docker ps -a -q -f name=$CONTAINER)" = "" ]; then
  echo "[INFO] Creating new SQL Server container..."
  docker run -e "ACCEPT_EULA=Y" \
             -e "SA_PASSWORD=$SA_PASSWORD" \
             -p $PORT:1433 \
             --name $CONTAINER \
             -d mcr.microsoft.com/mssql/server:2019-latest
else
  echo "[INFO] Container exists → starting..."
  docker start $CONTAINER || true
fi

echo "[INFO] Waiting for SQL Server to initialize..."
sleep 15

echo "==== 2. Ensure mssql-tools installed inside container ===="

docker exec -it $CONTAINER bash -c "
if [ ! -f /opt/mssql-tools/bin/sqlcmd ]; then
  echo '[INFO] Installing mssql-tools...'
  apt-get update
  apt-get install -y curl gnupg
  curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
  curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/msprod.list
  apt-get update
  ACCEPT_EULA=Y apt-get install -y mssql-tools unixodbc-dev
  echo 'export PATH=\$PATH:/opt/mssql-tools/bin' >> ~/.bashrc
else
  echo '[INFO] mssql-tools already installed.'
fi
"

echo "==== 3. Create backup directory ===="
docker exec -it $CONTAINER bash -c "mkdir -p /var/opt/mssql/backups && chmod 777 /var/opt/mssql/backups"

echo "==== 4. Copy .bak files into container ===="
docker cp WideWorldImporters-Full.bak   $CONTAINER:/var/opt/mssql/backups/
docker cp WideWorldImportersDW-Full.bak $CONTAINER:/var/opt/mssql/backups/

echo "==== 5. Restore database: WideWorldImporters ===="
docker exec -i $CONTAINER /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SA_PASSWORD" -Q "
IF DB_ID('WideWorldImporters') IS NOT NULL
    PRINT 'WideWorldImporters already restored';
ELSE
BEGIN
    RESTORE DATABASE WideWorldImporters
    FROM DISK='/var/opt/mssql/backups/WideWorldImporters-Full.bak'
    WITH MOVE 'WWI_Primary' TO '/var/opt/mssql/data/WideWorldImporters.mdf',
         MOVE 'WWI_UserData' TO '/var/opt/mssql/data/WideWorldImporters_UserData.ndf',
         MOVE 'WWI_Log' TO '/var/opt/mssql/data/WideWorldImporters_log.ldf',
         MOVE 'WWI_InMemory_Data_1' TO '/var/opt/mssql/data/WideWorldImporters_InMemory_Data_1',
         REPLACE, STATS=5;
END
"

echo "==== 6. Restore database: WideWorldImportersDW ===="
docker exec -i $CONTAINER /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SA_PASSWORD" -Q "
IF DB_ID('WideWorldImportersDW') IS NOT NULL
    PRINT 'WideWorldImportersDW already restored';
ELSE
BEGIN
    RESTORE DATABASE WideWorldImportersDW
    FROM DISK='/var/opt/mssql/backups/WideWorldImportersDW-Full.bak'
    WITH MOVE 'WWI_Primary' TO '/var/opt/mssql/data/WideWorldImportersDW.mdf',
         MOVE 'WWI_Log' TO '/var/opt/mssql/data/WideWorldImportersDW_log.ldf',
         REPLACE, STATS=5;
END
"

echo "==== 7. Verify restored DBs ===="
docker exec -i $CONTAINER /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SA_PASSWORD" -Q "SELECT name FROM sys.databases;"

echo "==== DONE — WideWorldImporters + WideWorldImportersDW are ready! ===="
echo "Connect using:"
echo "  Server=localhost,$PORT"
echo "  User=SA"
echo "  Password=$SA_PASSWORD"