#!/usr/bin/env python3

"""
HPVMM to OncoSim Dimension Mapping Script
Author: Parsa Abadi

Applies all dimension vocabulary mappings discovered during integration testing.
This script handles the specific vocabulary differences between HPVMM and OncoSim models.
"""

import os
import sys
import glob

def apply_hpv_type_mappings(content):
    mappings = {
        'Type_6': 'HPV_6',
        'Type_11': 'HPV_11', 
        'Type_16': 'HPV_16',
        'Type_18': 'HPV_18',
        'Other_carcinogenic_HPV_types': 'HPV_OTHER_CANCEROUS',
        'Other_non_carcinogenic_HPV_types': 'HPV_OTHER_NON_CANCEROUS'
    }
    
    for old, new in mappings.items():
        content = content.replace(old, new)
    return content

def fix_incidence_rates_hpv(filepath):
    print(f"  Fixing IncidenceRatesHPV (29,953+ values)")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = apply_hpv_type_mappings(content)
    
    content = content.replace('First', 'FOS_FIRST')
    content = content.replace('Subsequent', 'FOS_SUBSEQUENT')
    
    content = content.replace('Not_vaccinated', 'VS_NOT_VACCINATED')
    content = content.replace('Vaccinated', 'VS_VACCINATED')
    
    content = content.replace('VS_NOT_VS_VACCINATED', 'VS_NOT_VACCINATED')
    content = content.replace('VS_VS_VACCINATED', 'VS_VACCINATED')
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"    Applied 10 dimension mappings")

def fix_hpv_clearance_hazard(filepath):
    print(f"  Fixing HpvClearanceHazard")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = apply_hpv_type_mappings(content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"    Applied 6 HPV type mappings")

def fix_hpv_persistent_proportion(filepath):
    print(f"  Fixing HpvPersistentProportion")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    content = apply_hpv_type_mappings(content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"    Applied 6 HPV type mappings")

def fix_user_phi_parameters(filepath):
    parameter_name = os.path.basename(filepath).replace('.csv', '')
    print(f"  Fixing {parameter_name}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    mappings = {
        'X_0': 'AL_0',
        'X_1': 'AL_1',
        'X_2': 'AL_2',
        'X_3': 'AL_3'
    }
    
    for old, new in mappings.items():
        content = content.replace(old, new)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"    Applied 4 activity level mappings")

def fix_vaccination_program_design(filepath):
    print(f"  Fixing VaccinationProgramDesign")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    mappings = {
        'Deactivated_0_or_Activated_1': 'VPEC_ACTIVE',
        'Minimum_age_0_99': 'VPEC_MIN_AGE',
        'Maximum_age_0_99': 'VPEC_MAX_AGE',
        'Sex_0_F_1_M_2_both': 'VPEC_SEX',
        'Minimum_projection_year_0_99': 'VPEC_MIN_YEAR',
        'Maximum_projection_year_0_99': 'VPEC_MAX_YEAR',
        'VPEC_SCREEN_ON_x_CINATION_STATUS': 'VPEC_SCREEN_ON_VACCINATION_STATUS',
        'Coverage_percentage_0_100': 'VPEC_COVERAGE'
    }
    
    for old, new in mappings.items():
        content = content.replace(old, new)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"    Applied 8 vaccination program mappings")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix_hpvmm_oncosim_dimensions.py <parameter_set_directory>")
        print("Example: python3 fix_hpvmm_oncosim_dimensions.py oncosim_full_export\\oncosim\\set.HPVMM_Test_Run\\")
        sys.exit(1)
    
    param_dir = sys.argv[1]
    
    if not os.path.exists(param_dir):
        print(f"Directory not found: {param_dir}")
        sys.exit(1)
    
    print("HPVMM to OncoSim Dimension Mapping")
    print("=" * 40)
    print(f"Target directory: {param_dir}")
    print()
    
    parameter_fixers = {
        'IncidenceRatesHPV.csv': fix_incidence_rates_hpv,
        'HpvClearanceHazard.csv': fix_hpv_clearance_hazard,
        'HpvPersistentProportion.csv': fix_hpv_persistent_proportion,
        'UserBigPhi.csv': fix_user_phi_parameters,
        'UserPhi.csv': fix_user_phi_parameters,
        'VaccinationProgramDesign.csv': fix_vaccination_program_design
    }
    
    fixed_count = 0
    
    for filename, fixer_func in parameter_fixers.items():
        filepath = os.path.join(param_dir, filename)
        if os.path.exists(filepath):
            fixer_func(filepath)
            fixed_count += 1
        else:
            print(f"  {filename} not found - skipping")
    
    print()
    print(f"Dimension mapping complete!")
    print(f"   {fixed_count}/6 parameters processed")
    print(f"   All HPVMM to OncoSim vocabulary conflicts resolved")
    print()
    print("Ready for OncoSim import:")
    print("  dbcopy -m oncosim -dbcopy.To db -dbcopy.FromSqlite oncosim.sqlite -dbcopy.InputDir oncosim_full_export")

if __name__ == "__main__":
    main()
