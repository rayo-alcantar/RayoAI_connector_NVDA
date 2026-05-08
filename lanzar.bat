@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =====================================
REM Config
REM =====================================
set "REPO_OWNER=rayo-alcantar"
set "REPO_NAME=killprocess"
set "REPO=%REPO_OWNER%/%REPO_NAME%"
set "SCONS_CMD=scons"

REM =====================================
REM Verificaciones
REM =====================================
where git >nul 2>&1 || (echo ERROR: git no esta en PATH.& exit /b 1)
where gh  >nul 2>&1 || (echo ERROR: gh no esta en PATH.& exit /b 1)
where %SCONS_CMD% >nul 2>&1 || (echo ERROR: scons no esta en PATH.& exit /b 1)

REM =====================================
REM Version/tag
REM =====================================
set "VERSION="
set /p VERSION=Introduce la version/tag (ej: 2026.2.13): 
if "%VERSION%"=="" (
    echo ERROR: version vacia.
    exit /b 1
)

REM =====================================
REM Build
REM =====================================
echo.
echo ==== Ejecutando build ====
%SCONS_CMD%
if errorlevel 1 (
    echo ERROR: fallo el build.
    exit /b 1
)

REM =====================================
REM Detectar unico .nvda-addon
REM =====================================
set "ADDON_FILE="
for %%F in (*.nvda-addon) do (
    if defined ADDON_FILE (
        echo ERROR: hay mas de un .nvda-addon en la carpeta.
        exit /b 1
    )
    set "ADDON_FILE=%%F"
)

if not defined ADDON_FILE (
    echo ERROR: no se encontro ningun .nvda-addon.
    exit /b 1
)

echo Addon encontrado: %ADDON_FILE%

REM =====================================
REM Git commit/tag/push
REM =====================================
git add -A

git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Release %VERSION%"
)

git tag %VERSION% 2>nul
if errorlevel 1 (
    echo ERROR: el tag ya existe o no pudo crearse.
    exit /b 1
)

git push
git push origin %VERSION%

REM =====================================
REM Release en GitHub
REM =====================================
gh release view %VERSION% --repo %REPO% >nul 2>&1
if errorlevel 1 (
    gh release create %VERSION% "%ADDON_FILE%" --repo %REPO% --title "%VERSION%" --notes "Release %VERSION%"
) else (
    gh release upload %VERSION% "%ADDON_FILE%" --repo %REPO% --clobber
)

echo.
echo ==========================
echo Release publicada: %VERSION%
echo Archivo: %ADDON_FILE%
echo ==========================
pause
endlocal
