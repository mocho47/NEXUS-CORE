@echo off
title NEXUS v2
cd /d C:\nexus_v2
start "NEXUS v2 Server" python server.py
timeout /t 4 >nul
start http://localhost:8001
