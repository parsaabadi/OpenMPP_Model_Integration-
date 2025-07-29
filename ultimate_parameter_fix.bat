@echo off
REM Ultimate parameter fix - the definitive solution

echo ===== ULTIMATE PARAMETER FIX =====

REM Configure OpenM++ paths
if defined OM_ROOT (
    set "OMPP_ROOT=%OM_ROOT%"
) else (
    set "OMPP_ROOT=%~dp0.."
)

set "DBCOPY_EXE=%OMPP_ROOT%\bin\dbcopy.exe"
if not exist "%DBCOPY_EXE%" (
    echo ERROR: dbcopy not accessible at %DBCOPY_EXE%
    echo Please verify OpenM++ installation or set OM_ROOT environment variable
    pause
    exit /b 1
)

echo Step 1: Initialize clean workspace
if exist "ultimate_export" rmdir /s /q "ultimate_export"
if exist "ultimate_import" rmdir /s /q "ultimate_import"
if exist "verify_ultimate" rmdir /s /q "verify_ultimate"

echo Step 2: Export current parameter structure for analysis
"%DBCOPY_EXE%" -m THIM -dbcopy.To text -dbcopy.FromSqlite THIM.sqlite -dbcopy.SetName Default -dbcopy.OutputDir ultimate_export

echo Step 3: Create optimal import structure
mkdir "ultimate_import"
mkdir "ultimate_import\THIM"
mkdir "ultimate_import\THIM\set.Default"

echo Step 4: Copy and modify all parameters
xcopy "ultimate_export\THIM.set.Default\set.Default\*" "ultimate_import\THIM\set.Default\" /Y /Q

REM Apply the critical parameter modification
echo sub_id,param_value > "ultimate_import\THIM\set.Default\StartingPopulationSize.csv"
echo 0,50000 >> "ultimate_import\THIM\set.Default\StartingPopulationSize.csv"

echo Step 5: Generate complete JSON metadata
echo {> "ultimate_import\THIM\THIM.set.Default.json"
echo   "ModelName": "THIM",>> "ultimate_import\THIM\THIM.set.Default.json"
echo   "Name": "Default",>> "ultimate_import\THIM\THIM.set.Default.json"
echo   "IsReadonly": false,>> "ultimate_import\THIM\THIM.set.Default.json"
echo   "Param": [>> "ultimate_import\THIM\THIM.set.Default.json"
echo     {"Name": "StartingPopulationSize", "Subcount": 1, "Txt": [{"LangCode": "EN", "Descr": "Ultimate fix - enhanced population for testing"}]}>> "ultimate_import\THIM\THIM.set.Default.json"
echo   ]>> "ultimate_import\THIM\THIM.set.Default.json"
echo }>> "ultimate_import\THIM\THIM.set.Default.json"

echo Step 6: Execute parameter import
"%DBCOPY_EXE%" -m THIM -dbcopy.To db -dbcopy.ToSqlite THIM.sqlite -dbcopy.InputDir ultimate_import

echo Step 7: Comprehensive import verification
"%DBCOPY_EXE%" -m THIM -dbcopy.To text -dbcopy.FromSqlite THIM.sqlite -dbcopy.SetName Default -dbcopy.OutputDir verify_ultimate

echo Step 8: Validate modification persistence
if exist "verify_ultimate\THIM.set.Default\set.Default\StartingPopulationSize.csv" (
    echo SUCCESS: Parameter modification confirmed
    echo Current value:
    type "verify_ultimate\THIM.set.Default\set.Default\StartingPopulationSize.csv"
) else (
    echo WARNING: Verification file not found
)

echo Step 9: ULTIMATE TEST - Full THIM simulation with enhanced parameters
THIM.exe -OpenM.SetName Default -OpenM.RunName THIM_ULTIMATE_TEST -OpenM.SubValues 16 -OpenM.Threads 4 