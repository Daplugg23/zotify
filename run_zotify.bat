@echo off
cd /d %~dp0
call zotify_env\Scripts\activate.bat

if "%~1"=="" (
    powershell -Command "$url = Read-Host 'Enter Spotify URL'; python -m zotify $url"
) else (
    python -m zotify %*
)
pause