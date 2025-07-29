@echo off
REM THIM Parameter Modification Script
REM Modifies StartingPopulationSize parameter from 500 to 50,000
REM Requires full_model_export directory to exist (run dbcopy export first)

echo ===== THIM PARAMETER MODIFICATION =====
echo.
echo Modifying StartingPopulationSize parameter to 50,000...
echo.

echo Step 1: Create import structure
if exist "working_import" rmdir /s /q "working_import"
mkdir "working_import"
mkdir "working_import\THIM"
mkdir "working_import\THIM\set.Default"

echo Step 2: Copy metadata files
copy "full_model_export\THIM\THIM.lang.json" "working_import\THIM\" >nul
copy "full_model_export\THIM\THIM.model.json" "working_import\THIM\" >nul
copy "full_model_export\THIM\THIM.profile.json" "working_import\THIM\" >nul
copy "full_model_export\THIM\THIM.set.Default.json" "working_import\THIM\" >nul
copy "full_model_export\THIM\THIM.text.json" "working_import\THIM\" >nul
copy "full_model_export\THIM\THIM.word.json" "working_import\THIM\" >nul

echo Step 3: Copy parameter files
xcopy "full_model_export\THIM\set.Default\*" "working_import\THIM\set.Default\" /Y /Q >nul
del "working_import\THIM\set.Default\StartingPopulationSize.csv" >nul 2>&1

echo Step 4: Create modified StartingPopulationSize parameter
echo sub_id,param_value> "working_import\THIM\set.Default\StartingPopulationSize.csv"
echo 0,50000>> "working_import\THIM\set.Default\StartingPopulationSize.csv"

echo Step 5: Verify parameter value
type "working_import\THIM\set.Default\StartingPopulationSize.csv"

echo Step 6: Import modified parameters
echo Importing parameters into database...
..\..\bin\dbcopy -m THIM -dbcopy.To db -dbcopy.ToSqlite THIM.sqlite -dbcopy.InputDir working_import

echo Step 7: Verify import success
if exist "verify_working" rmdir /s /q "verify_working"
..\..\bin\dbcopy -m THIM -dbcopy.To text -dbcopy.FromSqlite THIM.sqlite -dbcopy.SetName Default -dbcopy.OutputDir verify_working >nul

if exist "verify_working\THIM.set.Default\set.Default\StartingPopulationSize.csv" (
    echo Parameter import successful
    echo Database value:
    type "verify_working\THIM.set.Default\set.Default\StartingPopulationSize.csv"
) else (
    echo Parameter import failed
    goto :end
)

echo Step 8: Run THIM simulation
echo.
echo Running THIM with modified parameters...
echo Expected result: entities should be ~84,000 instead of 843
echo.

THIM.exe -OpenM.SetName Default -OpenM.RunName THIM_Modified_Population -OpenM.SubValues 16 -OpenM.Threads 4

echo.
echo ===== MODIFICATION COMPLETE =====
echo.
echo Check the "entities=" count in the simulation summary above.
echo Success: entities ~84,000 | Failure: entities = 843
echo.

:end
pause 