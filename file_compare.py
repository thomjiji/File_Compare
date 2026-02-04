import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.exporters import export_to_json, export_to_txt, export_to_csv, export_to_html

def compare_simple(files1, files2):
    """
    Simple comparison that finds unique files in each group.
    
    Args:
        files1: Dictionary of files from first group
        files2: Dictionary of files from second group
    
    Returns:
        tuple: (unique1, unique2, frame_mismatches)
               frame_mismatches is always empty list for simple comparison
    """
    unique1 = set(files1.keys()) - set(files2.keys())
    unique2 = set(files2.keys()) - set(files1.keys())
    return unique1, unique2, []

def compare_advanced(files1, files2):
    """
    Advanced comparison for proxy mode with frame count verification.
    First performs simple comparison, then checks frame counts.
    
    Args:
        files1: Dictionary with frame count info from first group
        files2: Dictionary with frame count info from second group
    
    Returns:
        tuple: (unique1, unique2, frame_mismatches)
    """
    # First do the simple comparison
    unique1, unique2, _ = compare_simple(files1, files2)
    
    # Then check frame counts for common files
    keys1 = set(files1.keys())
    keys2 = set(files2.keys())
    common_keys = keys1 & keys2
    
    frame_mismatches = []
    for key in common_keys:
        file1_info = files1[key]
        file2_info = files2[key]
        
        frame1 = file1_info.get('frame_count')
        frame2 = file2_info.get('frame_count')
        
        # If frames match, skip (not a mismatch)
        if frame1 == frame2:
            continue
            
        # Determine difference value
        difference = "N/A"
        if isinstance(frame1, (int, float)) and isinstance(frame2, (int, float)):
            difference = abs(frame1 - frame2)
        elif frame1 is None:
            difference = "Source frame count missing"
        elif frame2 is None:
            difference = "Proxy frame count missing"
            
        mismatch = {
            'basename': key,
            'file1': file1_info['filename'],
            'file2': file2_info['filename'],
            'frames1': frame1,
            'frames2': frame2,
            'difference': difference,
            'path1': file1_info['path'],
            'path2': file2_info['path']
        }
        frame_mismatches.append(mismatch)
    
    return unique1, unique2, frame_mismatches

def main():
    parser = argparse.ArgumentParser(
        description='Compare files between directories with support for video proxy workflows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Modes:
  normal    Compare all files by full filename (default)
  proxy     Compare video files by basename only
  proxyadv  Proxy mode with frame count verification (requires mediainfo)

Examples:
  %(prog)s /path/to/dir1 /path/to/dir2
  %(prog)s -m proxy /originals /proxies
  %(prog)s -m proxyadv -f html /originals /proxies
  %(prog)s "/dir1+/dir2" "/dir3"  # Compare combined directories
        '''
    )
    
    parser.add_argument('path1', help='First directory or directories (use + to combine multiple)')
    parser.add_argument('path2', help='Second directory or directories (use + to combine multiple)')
    parser.add_argument('-f', '--format', choices=['json', 'txt', 'csv', 'html'], 
                       default=['html'], nargs='+', help='Output format(s) (default: html)')
    parser.add_argument('-m', '--mode', choices=['normal', 'proxy', 'proxyadv'],
                       default='normal', help='Comparison mode (default: normal)')
    
    args = parser.parse_args()
    
    # Import the appropriate comparison module based on mode
    if args.mode == 'proxy':
        from src.proxy_compare import get_files_dict
        print("Mode: Proxy comparison (by basename only)")
        mode_name = 'proxy'
    elif args.mode == 'proxyadv':
        from src.proxy_compare_advanced import get_files_dict
        print("Mode: Advanced proxy comparison (with frame verification)")
        mode_name = 'proxy_advanced'
    else:
        from src.normal_compare import get_files_dict
        print("Mode: Normal comparison")
        mode_name = 'normal'
    
    # Parse paths
    paths1 = [p.strip() for p in args.path1.split('+')]
    paths2 = [p.strip() for p in args.path2.split('+')]
    
    # Display paths being compared
    print(f"\nGroup 1 ({len(paths1)} path{'s' if len(paths1) > 1 else ''}):")
    for p in paths1:
        print(f"  - {p}")
    
    print(f"\nGroup 2 ({len(paths2)} path{'s' if len(paths2) > 1 else ''}):")
    for p in paths2:
        print(f"  - {p}")
    
    # Validate all paths
    all_paths = paths1 + paths2
    for path in all_paths:
        if not os.path.exists(path):
            print(f"\nError: Path does not exist: {path}")
            return 1
    
    # Scan directories
    print("\nScanning directories...")
    files1 = {}
    files2 = {}
    
    # Scan group 1
    for path in paths1:
        print(f"Scanning: {path}")
        files = get_files_dict(path)
        for key, value in files.items():
            if key not in files1:
                files1[key] = value
    
    # Scan group 2
    for path in paths2:
        print(f"Scanning: {path}")
        files = get_files_dict(path)
        for key, value in files.items():
            if key not in files2:
                files2[key] = value
    
    print(f"\nFound {len(files1)} unique items in group 1")
    print(f"Found {len(files2)} unique items in group 2")
    
    # Compare files using the appropriate comparison function
    if args.mode == 'proxyadv':
        unique1, unique2, frame_mismatches = compare_advanced(files1, files2)
        print(f"Frame count mismatches found: {len(frame_mismatches)}")
    else:
        unique1, unique2, frame_mismatches = compare_simple(files1, files2)
    
    print(f"\nComparison Results:")
    print(f"Files only in group 1: {len(unique1)}")
    print(f"Files only in group 2: {len(unique2)}")
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Prepare data for the exporters (matching the structure they expect)
    # Get full paths for unique files
    unique1_full_paths = []
    for key in unique1:
        if args.mode == 'proxyadv':
            unique1_full_paths.append(files1[key]['path'])
        else:
            unique1_full_paths.append(files1[key])

    unique2_full_paths = []
    for key in unique2:
        if args.mode == 'proxyadv':
            unique2_full_paths.append(files2[key]['path'])
        else:
            unique2_full_paths.append(files2[key])

    export_data = {
        'mode': mode_name,
        'path1': args.path1,
        'path2': args.path2,
        'dirs1': paths1,
        'dirs2': paths2,
        'unique1': sorted(unique1_full_paths),
        'unique2': sorted(unique2_full_paths)
    }
        
    # Add frame mismatches if present
    if frame_mismatches:
        export_data['frame_mismatches'] = frame_mismatches
    
    # Export results for each requested format
    generated_files = []
    for fmt in args.format:
        output_filename = f"comparison_results_{timestamp}.{fmt}"
        output_path = Path(output_filename).resolve()
        
        if fmt == 'json':
            export_to_json(export_data, output_filename)
        elif fmt == 'csv':
            export_to_csv(export_data, output_filename)
        elif fmt == 'html':
            export_to_html(export_data, output_filename)
        else:  # txt
            export_to_txt(export_data, output_filename)
        
        generated_files.append(str(output_path))
    
    print(f"\nResults exported to:")
    for path in generated_files:
        print(f"  - {path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())