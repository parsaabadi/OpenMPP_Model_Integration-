# HPVMM to OncoSim Integration Pipeline

**Author: Parsa Abadi**

Automated pipeline for integrating HPVMM simulation data into OncoSim models on Windows systems.

## Quick Start

### Prerequisites
- Windows with OpenM++ installed
- Completed HPVMM simulation
- Python 3 
### Automated Integration

1. **Convert HPVMM data to OncoSim parameters**
   ```cmd
   python create_import_set.py --imports hpvmm_oncosim_imports.csv --upstream hpvmm --run HPVMM_Test_Run --downstream oncosim
   ```

2. **Run complete integration pipeline**
   ```cmd
   hpvmm_oncosim_pipeline.bat HPVMM_Test_Run
   ```

### Manual Steps (if automation fails)

1. **Export OncoSim structure**
   ```cmd
   dbcopy -m oncosim -dbcopy.FromSqlite oncosim.sqlite -dbcopy.To text -dbcopy.OutputDir oncosim_full_export
   ```

2. **Extract parameter files**
   ```cmd
   powershell Expand-Archive oncosim.set.HPVMM_Test_Run.zip -DestinationPath temp_extract
   mkdir oncosim_full_export\oncosim\set.HPVMM_Test_Run
   copy temp_extract\oncosim.set.HPVMM_Test_Run\set.HPVMM_Test_Run\*.csv oncosim_full_export\oncosim\set.HPVMM_Test_Run\
   ```

3. **Fix dimension mappings**
   ```cmd
   python fix_hpvmm_oncosim_dimensions.py oncosim_full_export\oncosim\set.HPVMM_Test_Run\
   ```

4. **Import into OncoSim**
   ```cmd
   dbcopy -m oncosim -dbcopy.To db -dbcopy.FromSqlite oncosim.sqlite -dbcopy.InputDir oncosim_full_export
   ```

5. **Run OncoSim with HPVMM data**
   ```cmd
   oncosim.exe -OpenM.SetName HPVMM_Test_Run -OpenM.RunName OncoSim_With_HPVMM -OpenM.SubValues 1
   ```

## Files

- `create_import_set.py` - Core parameter conversion tool
- `hpvmm_oncosim_imports.csv` - Parameter mapping configuration
- `hpvmm_oncosim_pipeline.bat` - Complete automation script
- `fix_hpvmm_oncosim_dimensions.py` - Dimension vocabulary fixing

## Dimension Mappings

The pipeline automatically fixes vocabulary differences between HPVMM and OncoSim:

**HPV Types:** Type_6 → HPV_6, Other_carcinogenic_HPV_types → HPV_OTHER_CANCEROUS

**Activity Levels:** X_0 → AL_0, X_1 → AL_1, X_2 → AL_2, X_3 → AL_3

**Vaccination Status:** Not_vaccinated → VS_NOT_VACCINATED, Vaccinated → VS_VACCINATED

**Program Elements:** Deactivated_0_or_Activated_1 → VPEC_ACTIVE, Minimum_age_0_99 → VPEC_MIN_AGE

## Troubleshooting

**Parameter not found:** Verify HPVMM simulation completed and IM_* tables exist
**Invalid value errors:** Check if new dimension mappings need to be added
**Import failures:** Ensure OncoSim database is accessible and not in use
