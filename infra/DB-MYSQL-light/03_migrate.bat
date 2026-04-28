@echo off
REM Applies V2 + V3 migrations in sequence:
REM   V2 — normalize genres into movie_genres junction table
REM   V3 — convert all tables to InnoDB and add foreign key constraints
setlocal

set "CONTAINER_NAME=mysql_imdb_light"
set "MYSQL_ROOT_PASSWORD=YourStrong!Passw0rd"
set "SCRIPT_DIR=%~dp0"

echo [V2] Normalizing genres...
docker exec -i ^
    -e MYSQL_PWD="%MYSQL_ROOT_PASSWORD%" ^
    "%CONTAINER_NAME%" ^
    mysql -uroot --protocol=TCP --host=127.0.0.1 imdb ^
    < "%SCRIPT_DIR%migrations\V2__normalize_genres.sql"
if errorlevel 1 (echo ERROR: V2 failed & exit /b 1)
echo [V2] Done.

echo [V3] Converting to InnoDB and adding foreign keys...
docker exec -i ^
    -e MYSQL_PWD="%MYSQL_ROOT_PASSWORD%" ^
    "%CONTAINER_NAME%" ^
    mysql -uroot --protocol=TCP --host=127.0.0.1 imdb ^
    < "%SCRIPT_DIR%migrations\V3__innodb_and_fk.sql"
if errorlevel 1 (echo ERROR: V3 failed & exit /b 1)
echo [V3] Done.

echo.
echo Migration complete. All tables are now InnoDB with referential integrity.
echo Verify: mysql -h 127.0.0.1 -P 3307 -uroot -p"%MYSQL_ROOT_PASSWORD%" imdb ^< verify.sql
