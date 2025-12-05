@echo off
REM Deploy script wrapper / デプロイスクリプトのラッパー
REM Uses Windows PowerShell to run deploy.ps1 / Windows PowerShell を使用して deploy.ps1 を実行します
powershell.exe -ExecutionPolicy RemoteSigned -File "%~dp0deploy.ps1" %*
