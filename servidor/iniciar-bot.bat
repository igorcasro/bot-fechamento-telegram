@echo off
rem Mantem o bot rodando: se ele encerrar por qualquer motivo, espera 15 s e liga de novo.
rem Quem chama este arquivo e o Agendador de Tarefas (veja instalar-windows.ps1).
rem Para testar a mao: de dois cliques ou rode "servidor\iniciar-bot.bat" (Ctrl+C para parar).

cd /d "%~dp0.."
if not exist logs mkdir logs

:inicio
echo [%date% %time%] Iniciando o bot >> logs\servico.log
".venv\Scripts\python.exe" bot.py 2>> logs\erro-saida.log
echo [%date% %time%] O bot encerrou (codigo %errorlevel%). Reiniciando em 15 s >> logs\servico.log
rem "ping" faz a pausa porque o "timeout" falha quando nao ha janela (tarefa em segundo plano)
ping -n 16 127.0.0.1 >nul
goto inicio
