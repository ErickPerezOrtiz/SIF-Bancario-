@echo off
:: ============================================================
::  SIF-Bancario — Setup automático (Windows)
::  Ejecutar con doble clic después de instalar Python y MySQL
:: ============================================================
echo.
echo  ================================================
echo   SIF-Bancario :: Setup del Entorno
echo   Portafolio de Erick Perez - ITLA
echo  ================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado. Instala desde https://www.python.org/downloads/
    pause & exit /b 1
)
echo [OK] Python detectado.

:: Crear entorno virtual
if not exist venv (
    echo [INFO] Creando entorno virtual...
    python -m venv venv
)
echo [OK] Entorno virtual listo.

:: Activar e instalar dependencias
call venv\Scripts\activate.bat
echo [INFO] Instalando dependencias...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo [OK] Dependencias instaladas.

:: Copiar .env si no existe
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Archivo .env creado. EDITA .env con tu API Key y credenciales MySQL.
) else (
    echo [INFO] .env ya existe.
)

echo.
echo  ================================================
echo   PASOS SIGUIENTES:
echo   1. Edita el archivo .env con:
echo      - SB_API_KEY  (tu Ocp-Apim-Subscription-Key)
echo      - DB_PASSWORD (tu password de MySQL)
echo   2. Ejecuta: python main.py test-api
echo   3. Ejecuta: python main.py etl
echo   4. Ejecuta: python main.py dashboard
echo  ================================================
echo.
pause
