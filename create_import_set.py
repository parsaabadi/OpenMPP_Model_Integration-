#!/usr/bin/env python3

import argparse
import os
import sys
import json
import zipfile
import csv
import shutil
import re
from pathlib import Path

script_name = 'create_import_set'
script_version = '1.1'

def detect_csv_format(csv_lines):
    if not csv_lines:
        return 'unknown', []
    
    header_line = csv_lines[0].strip()
    if header_line.startswith('\ufeff'):
        header_line = header_line[1:]
    
    reader = csv.reader([header_line])
    header_fields = next(reader)
    
    if ('expr_name' in header_fields and 'expr_value' in header_fields):
        return 'expression', header_fields
    
    if ('sub_id' in header_fields and 'acc_value' in header_fields):
        return 'accumulator', header_fields
    
    if header_fields and header_fields[0] == 'sub_id' and header_fields[-1] in ['acc_value', 'Value']:
        return 'accumulator', header_fields
    
    return 'unknown', header_fields

def convert_expression_to_accumulator(csv_lines, table_name):
    if not csv_lines:
        return []
    
    reader = csv.reader(csv_lines)
    header = next(reader)
    
    if header and header[0].startswith('\ufeff'):
        header[0] = header[0][1:]
    
    acc_header = ['sub_id']
    
    for field in header:
        if field not in ['expr_name', 'expr_value']:
            acc_header.append(field)
    
    acc_header.extend(['acc_id', 'acc_value'])
    
    acc_rows = [acc_header]
    
    for row in reader:
        if len(row) < len(header):
            continue
            
        acc_row = ['0']
        
        for i, field in enumerate(header):
            if field not in ['expr_name', 'expr_value']:
                acc_row.append(row[i] if i < len(row) else '')
        
        acc_row.append('0')
        
        value_idx = -1
        for i, field in enumerate(header):
            if field == 'expr_value':
                value_idx = i
                break
        
        if value_idx >= 0 and value_idx < len(row):
            acc_row.append(row[value_idx])
        else:
            acc_row.append('0')
        
        acc_rows.append(acc_row)
    
    output_lines = []
    for row in acc_rows:
        import io
        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(row)
        output_lines.append(output.getvalue().strip())
    
    return output_lines

def main():
    parser = argparse.ArgumentParser(
        description=f'{script_name} - Create parameter set from upstream model output'
    )
    parser.add_argument('--version', '-v', action='version', version=f'{script_name} version {script_version}')
    parser.add_argument('--imports', '-i', required=True, help='Path of model imports csv file')
    parser.add_argument('--upstream', '-u', required=True, help='Name of upstream model')
    parser.add_argument('--run', '-r', required=True, help='Name of upstream model run')
    parser.add_argument('--downstream', '-d', required=True, help='Name of downstream model')
    parser.add_argument('--workdir', '-w', default='.', help='Path of working directory for zips (default: current directory)')
    parser.add_argument('--keep', action='store_true', help='Keep and propagate all subs')
    parser.add_argument('--verbose', action='store_true', help='Verbose log output')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.imports):
        print(f"Error: model imports file {args.imports} not found", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.workdir):
        print(f"Error: working directory {args.workdir} not found", file=sys.stderr)
        sys.exit(1)
    
    run_in_zip = os.path.join(args.workdir, f"{args.upstream}.run.{args.run}.zip")
    if not os.path.isfile(run_in_zip):
        print(f"Error: upstream run file {run_in_zip} not found", file=sys.stderr)
        sys.exit(1)
    
    verbose = args.verbose
    
    try:
        with zipfile.ZipFile(run_in_zip, 'r') as zip_in:
            if verbose:
                print(f"\n{len(zip_in.namelist())} members in run zip")
            
            json_files = [name for name in zip_in.namelist() if name.endswith('.json')]
            if len(json_files) != 1:
                print(f"Error: {len(json_files)} matches for json metadata file in run zip", file=sys.stderr)
                sys.exit(1)
            
            json_content = zip_in.read(json_files[0]).decode('utf-8')
            if verbose:
                print(f"run_zip_json length={len(json_content)}")
            
            try:
                metadata = json.loads(json_content)
            except json.JSONDecodeError as e:
                print(f"Error: failed to parse JSON metadata: {e}", file=sys.stderr)
                sys.exit(1)
            
            upstream_model_name = metadata.get('ModelName', '')
            if upstream_model_name != args.upstream:
                print(f"Error: incoherence between upstream model name {args.upstream} and model name inside run zip {upstream_model_name}", file=sys.stderr)
                sys.exit(1)
            
            run_zip_run_name = metadata.get('Name', '')
            if run_zip_run_name != args.run:
                print(f"Error: incoherence between upstream run name {args.run} and run name inside run zip {run_zip_run_name}", file=sys.stderr)
                sys.exit(1)
            
            upstream_subcount = metadata.get('SubCount', 1)
            upstream_lang_code = metadata.get('LangCode', 'EN')
            
            if verbose:
                print(f"run_zip_model_name = {upstream_model_name}")
                print(f"run_zip_run_name={run_zip_run_name}")
                print(f"upstream_subcount={upstream_subcount}")
                print(f"upstream_lang_code={upstream_lang_code}")
            
            set_name = args.run
            
            zip_out_topdir = f"{args.downstream}.set.{set_name}"
            zip_out_csvdir = os.path.join(zip_out_topdir, f"set.{set_name}")
            zip_out_json = os.path.join(zip_out_topdir, f"{args.downstream}.set.{set_name}.json")
            
            original_cwd = os.getcwd()
            os.chdir(args.workdir)
            
            try:
                if os.path.exists(zip_out_topdir):
                    shutil.rmtree(zip_out_topdir)
                
                os.makedirs(zip_out_topdir, exist_ok=True)
                os.makedirs(zip_out_csvdir, exist_ok=True)
                
                set_json_data = {
                    "ModelName": args.downstream,
                    "Name": set_name,
                    "IsReadonly": True,
                    "Param": []
                }
                
                parameters_processed = 0
                
                with open(args.imports, 'r') as imports_file:
                    reader = csv.DictReader(imports_file)
                    
                    for row in reader:
                        parameter_name = row['parameter_name']
                        parameter_rank = int(row['parameter_rank'])
                        from_name = row['from_name']
                        from_model_name = row['from_model_name']
                        is_sample_dim = row['is_sample_dim'].upper() == 'TRUE'
                        
                        table_rank = parameter_rank - (1 if is_sample_dim else 0)
                        
                        if from_model_name == args.upstream:
                            parameters_processed += 1
                            
                            if verbose:
                                print(f"\ncreating {parameter_name} from {from_name}")
                            
                            if is_sample_dim:
                                subcount = 1
                            elif args.keep:
                                subcount = upstream_subcount
                            else:
                                subcount = 1
                            
                            param_info = {
                                "Name": parameter_name,
                                "Subcount": subcount,
                                "Txt": [
                                    {
                                        "LangCode": upstream_lang_code,
                                        "Descr": f"{args.upstream}: {args.run}"
                                    }
                                ]
                            }
                            set_json_data["Param"].append(param_info)
                            
                            out_header = ["sub_id"]
                            for i in range(parameter_rank):
                                out_header.append(f"Dim{i}")
                            out_header.append("param_value")
                            
                            if verbose:
                                print(f"out_header = {','.join(out_header)}")
                            
                            table_pattern_acc = f".*/{from_name}.acc-all.csv"
                            table_pattern_expr = f".*/{from_name}.csv"
                            
                            matching_files = [name for name in zip_in.namelist() 
                                            if re.match(table_pattern_acc, name) or re.match(table_pattern_expr, name)]
                            
                            if len(matching_files) == 0:
                                print(f"Error: no matches for table {from_name} in run zip", file=sys.stderr)
                                sys.exit(1)
                            elif len(matching_files) > 1:
                                acc_files = [name for name in matching_files if name.endswith('.acc-all.csv')]
                                if acc_files:
                                    matching_files = acc_files[:1]
                                else:
                                    matching_files = matching_files[:1]
                            
                            zip_member = matching_files[0]
                            zip_out_csv = os.path.join(zip_out_csvdir, f"{parameter_name}.csv")
                            
                            if verbose:
                                print(f"zip_out_csv = {zip_out_csv}")
                            
                            csv_content = zip_in.read(zip_member).decode('utf-8')
                            csv_lines = csv_content.strip().split('\n')
                            
                            if verbose:
                                print(f"Read {len(csv_lines)} lines from {zip_member}")
                            
                            format_type, header_fields = detect_csv_format(csv_lines)
                            
                            if verbose:
                                print(f"Detected format: {format_type}")
                                print(f"Header fields: {header_fields}")
                            
                            if format_type == 'expression':
                                if verbose:
                                    print(f"Converting {from_name} from expression format to accumulator format")
                                csv_lines = convert_expression_to_accumulator(csv_lines, from_name)
                            elif format_type == 'unknown':
                                print(f"Warning: unknown CSV format for {from_name}, attempting to process as accumulator format")
                            
                            with open(zip_out_csv, 'w', newline='', encoding='utf-8') as out_file:
                                writer = csv.writer(out_file)
                                writer.writerow(out_header)
                                
                                reader = csv.reader(csv_lines)
                                in_header = next(reader)
                                
                                if in_header and in_header[0].startswith('\ufeff'):
                                    in_header[0] = in_header[0][1:]
                                
                                if verbose:
                                    print(f"in_header = {','.join(in_header)}")
                                
                                for line in reader:
                                    if not line or len(line) == 0:
                                        continue
                                    
                                    try:
                                        sub_id = int(line[0]) if line[0] else 0
                                        
                                        out_fields = []
                                        
                                        if is_sample_dim:
                                            out_fields.append('0')
                                            out_fields.append(str(sub_id))
                                        elif args.keep:
                                            out_fields.append(str(sub_id))
                                        else:
                                            if sub_id != 0:
                                                continue
                                            out_fields.append(str(sub_id))
                                        
                                        for dim in range(table_rank):
                                            if dim + 1 < len(line):
                                                out_fields.append(line[dim + 1])
                                            else:
                                                out_fields.append('0')
                                        
                                        if len(line) > 0:
                                            out_fields.append(line[-1])
                                        else:
                                            out_fields.append('0')
                                        
                                        writer.writerow(out_fields)
                                        
                                    except (ValueError, IndexError) as e:
                                        if verbose:
                                            print(f"Warning: skipping malformed line: {line} ({e})")
                                        continue
                
                with open(zip_out_json, 'w', encoding='utf-8') as json_file:
                    json.dump(set_json_data, json_file, indent=2)
                
                zip_out_name = f"{args.downstream}.set.{set_name}.zip"
                with zipfile.ZipFile(zip_out_name, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for root, dirs, files in os.walk(zip_out_topdir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, '.')
                            zip_out.write(file_path, arc_name)
                
                shutil.rmtree(zip_out_topdir)
                
                print(f"{parameters_processed} downstream {args.downstream} parameters created from upstream {args.upstream} tables")
                
            finally:
                os.chdir(original_cwd)
                
    except zipfile.BadZipFile:
        print(f"Error: {run_in_zip} is not a valid zip file", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 