REM Generate and run KILL statements for queries running > 30 seconds
SET DB_USER=root
SET DB_PASS=YourStrong!Passw0rd
SET DB_HOST=localhost
SET DB_PORT=3307
SET DB_NAME=imdb
IF "%CONTAINER_NAME%"=="" SET CONTAINER_NAME=mysql_imdb_light
docker exec %CONTAINER_NAME% mysql -u %DB_USER% -p%DB_PASS% -h %DB_HOST% -P %DB_PORT% --skip-column-names -e "SELECT CONCAT('KILL QUERY ', id, ';') FROM information_schema.processlist WHERE command != 'Sleep' AND time > 30 AND user NOT IN ('replication', 'event_scheduler');" | docker exec -i %CONTAINER_NAME% mysql -u %DB_USER% -p%DB_PASS% -h %DB_HOST% -P %DB_PORT%
