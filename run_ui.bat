@echo off
REM ----------------------------------------------------------------------------------------------------------------------
if "%1"=="" (set port=8000) else (set port=%1)
echo Chainlit http://localhost:%port%
set BROWSER=
chainlit run src/common/chainlit_app.py --port %port% 2>&1 | findstr /V /B /C:"gio:"