@echo off
REM Spins up mysql-imdb-light on port 3307 and loads the V1 seed schema.
REM No file downloads needed — all data is embedded in V1__initial_schema.sql.
setlocal

set "IMAGE_NAME=mysql-imdb-light:8.0"
set "CONTAINER_NAME=mysql_imdb_light"
set "MYSQL_ROOT_PASSWORD=YourStrong!Passw0rd"
set "HOST_PORT=3307"
set "SCRIPT_DIR=%~dp0"
set "V1_SQL=%SCRIPT_DIR%migrations\V1__initial_schema.sql"

REM Check docker is available
where docker >nul 2>&1
if errorlevel 1 (echo ERROR: docker not found & exit /b 1)

REM Build image if it doesn't exist yet
docker image inspect "%IMAGE_NAME%" >nul 2>&1
if errorlevel 1 (
    echo Building image %IMAGE_NAME%...
    call "%SCRIPT_DIR%01_build.bat"
)

REM Remove any existing container with the same name
docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Removing existing container %CONTAINER_NAME%...
    docker rm -f "%CONTAINER_NAME%" >nul
)

REM Start fresh container on port 3307
echo Starting %CONTAINER_NAME% on port %HOST_PORT%...
docker run -d ^
    --name "%CONTAINER_NAME%" ^
    -e MYSQL_ROOT_PASSWORD="%MYSQL_ROOT_PASSWORD%" ^
    -e MYSQL_ROOT_HOST="%" ^
    -p "%HOST_PORT%:3306" ^
    "%IMAGE_NAME%"

REM Wait for MySQL to become ready (up to 60 s)
echo Waiting for MySQL...
set /a i=0
:wait_loop
set /a i+=1
if %i% gtr 60 (
    echo ERROR: MySQL did not become ready in time.
    docker logs "%CONTAINER_NAME%"
    exit /b 1
)
docker exec -e MYSQL_PWD="%MYSQL_ROOT_PASSWORD%" "%CONTAINER_NAME%" ^
    mysqladmin ping -h127.0.0.1 >nul 2>&1
if errorlevel 1 (
    timeout /t 2 >nul
    goto wait_loop
)
echo MySQL is ready.

REM Load V1: schema + 50-movie seed dataset
echo Loading V1 schema and seed data...
docker exec -i ^
    -e MYSQL_PWD="%MYSQL_ROOT_PASSWORD%" ^
    "%CONTAINER_NAME%" ^
    mysql -uroot --protocol=TCP --host=127.0.0.1 ^
    < "%V1_SQL%"
if errorlevel 1 (echo ERROR: V1 import failed & exit /b 1)

echo.
echo  V1 loaded  — flat MyISAM schema, 50 movies seeded.
echo.
echo  Connect:
echo    mysql -h 127.0.0.1 -P %HOST_PORT% -uroot -p"%MYSQL_ROOT_PASSWORD%" imdb
echo.
echo  SQLAlchemy:
echo    DB_CONNECTION=mysql+pymysql://root:%MYSQL_ROOT_PASSWORD%@localhost:%HOST_PORT%/imdb
echo.
echo  Migration steps:
echo    03_migrate.bat   -- run V2 + V3 migrations (genres, InnoDB, foreign keys)
echo.
echo  Verify state at any time:
echo    mysql -h 127.0.0.1 -P %HOST_PORT% -uroot -p"%MYSQL_ROOT_PASSWORD%" imdb ^< verify.sql
