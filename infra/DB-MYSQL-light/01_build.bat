@echo off
REM Builds the mysql-imdb-light:8.0 Docker image.
set "IMAGE_NAME=mysql-imdb-light:8.0"
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
echo Building %IMAGE_NAME%...
docker build -t "%IMAGE_NAME%" "%SCRIPT_DIR%"
echo Built: %IMAGE_NAME%
