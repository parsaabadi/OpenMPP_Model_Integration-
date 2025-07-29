@echo off
REM Working parameter fix - handles directory structure properly

echo ===== WORKING PARAMETER FIX =====

REM Configure OpenM++ paths
if defined OM_ROOT (
    set "OMPP_ROOT=%OM_ROOT%"
) else (
    set "OMPP_ROOT=%~dp0.."
)

set "DBCOPY_EXE=%OMPP_ROOT%\bin\dbcopy.exe"
if not exist "%DBCOPY_EXE%" (
    echo ERROR: dbcopy not found at %DBCOPY_EXE%
    echo Please set OM_ROOT environment variable or run from OpenMPP\Perl directory
    pause
    exit /b 1
)

echo Step 1: Clean up any existing directories
if exist "temp_default" rmdir /s /q "temp_default"
if exist "fixed_import" rmdir /s /q "fixed_import"

echo Step 2: Export the Default parameter set
"%DBCOPY_EXE%" -m THIM -dbcopy.To text -dbcopy.FromSqlite THIM.sqlite -dbcopy.SetName Default -dbcopy.OutputDir temp_default

echo Step 3: Show current StartingPopulationSize value
type "temp_default\THIM.set.Default\set.Default\StartingPopulationSize.csv"

echo Step 4: Modify StartingPopulationSize to 50000
echo sub_id,param_value > "temp_default\THIM.set.Default\set.Default\StartingPopulationSize.csv"
echo 0,50000 >> "temp_default\THIM.set.Default\set.Default\StartingPopulationSize.csv"
echo New value:
type "temp_default\THIM.set.Default\set.Default\StartingPopulationSize.csv"

echo Step 5: Create proper import directory structure
mkdir "fixed_import"
mkdir "fixed_import\THIM"

echo Step 6: Copy the modified parameter set to correct location
xcopy "temp_default\THIM.set.Default\*" "fixed_import\THIM\" /E /Y /Q

echo Step 7: Show the fixed import structure
tree fixed_import /F

echo Step 8: Import the modified parameters
"%DBCOPY_EXE%" -m THIM -dbcopy.To db -dbcopy.ToSqlite THIM.sqlite -dbcopy.InputDir fixed_import

echo Step 9: Verify the import worked
if exist "verify_final" rmdir /s /q "verify_final"
"%DBCOPY_EXE%" -m THIM -dbcopy.To text -dbcopy.FromSqlite THIM.sqlite -dbcopy.SetName Default -dbcopy.OutputDir verify_final

echo Checking final value:
type "verify_final\THIM.set.Default\set.Default\StartingPopulationSize.csv"

echo Step 10: Run THIM to test the fix
THIM.exe -OpenM.SetName Default -OpenM.RunName THIM_Working_Fix -OpenM.SubValues 16 -OpenM.Threads 4 