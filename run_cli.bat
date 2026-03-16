@echo off
REM ----------------------------------------------------------------------------------------------------------------------
set "my_name=%~nx0"
set "agent_name=%~1"
set "query=%~2"
set "llm_provider=%~3"
REM ----------------------------------------------------------------------------------------------------------------------
set "agents_path=src\agents"
REM ----------------------------------------------------------------------------------------------------------------------
if "%agent_name%"=="" (
    echo Error: agent_name is required
    echo.
    call :usage
    call :list_available_agents
    exit /b 1
)
REM ----------------------------------------------------------------------------------------------------------------------
if not exist "%agents_path%\%agent_name%.py" (
    echo Error: Agent '%agent_name%' not found at %agents_path%\%agent_name%.py
    echo.
    call :usage
    call :list_available_agents
    exit /b 1
)
REM ----------------------------------------------------------------------------------------------------------------------
if "%query%"=="" (
    echo Error: query is required
    call :usage
    exit /b 1
)
REM ----------------------------------------------------------------------------------------------------------------------
if not "%llm_provider%"=="" (
    python %agents_path%\%agent_name%.py "%query%" "%llm_provider%"
) else (
    python %agents_path%\%agent_name%.py "%query%"
)
exit /b 0
REM ----------------------------------------------------------------------------------------------------------------------
:usage
echo Usage: %my_name% agent_name query [llm_provider: openai^|gemini^|anthropic]
exit /b 0
REM ----------------------------------------------------------------------------------------------------------------------
:list_available_agents
echo See available agents:
for %%f in (%agents_path%\*.py) do (
    echo   - %%~nf
)
exit /b 0