#!/usr/bin/env python3

import os
import sys
import time
import argparse

# Colors for console output
GREEN = '\033[92m'
BLUE = '\033[94m'
RESET = '\033[0m'

EXTENSIONS = [".xml", ".vbs", ".bat", ".ps1", ".py"]
DEFAULT_SEARCH_TERMS = ["adm", "password", "pwd"]

def print_help():
    print("""
    SYSVOL scout

    Usage:
    -mount <SMB mount directory>       Specify the SYSVOL SMB mount directory.
    -search <comma-separated terms>    Specify additional search terms.
    -sleep <time in seconds>           Specify delay between file reads to avoid overloading (default is 0.01s). Use 0 to disable.
    -h, -help, --help                  Display this help menu.
    """)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-mount", type=str, help="Specify the SYSVOL SMB mount directory.")
    parser.add_argument("-search", type=str, help="Specify additional search terms.")
    parser.add_argument("-sleep", type=float, default=0.01, help="Specify delay between file reads.")
    args = parser.parse_args()

    if not args.mount or ('-h' in sys.argv) or ('-help' in sys.argv) or ('--help' in sys.argv):
        print_help()
        sys.exit()

    mount_dir = args.mount
    sleep_time = args.sleep
    search_terms = DEFAULT_SEARCH_TERMS
    if args.search:
        search_terms += args.search.split(',')

    matched_files = {}
    found_files = {}
    spwd_files = []

    for subdir, _, files in os.walk(mount_dir):
        for file in files:
            time.sleep(sleep_time)

            # Check for the presence of "sPwd" in all files
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as f:
                content = f.read().decode('utf-8', 'replace').lower()
            if "spwd" in content:
                spwd_files.append((full_path, [line for line in content.splitlines() if "spwd" in line]))

            ext = os.path.splitext(file)[1]
            if ext in EXTENSIONS:

                try:
                    with open(full_path, 'rb') as f:
                        content = f.read().decode('utf-8', 'replace').lower()
                except OSError as e:
                    print(f"Warning: Unable to read {full_path}. Error: {e}")
                    continue

                if any(term in content for term in search_terms):
                    matched_files.setdefault(ext, []).append(full_path)
                else:
                    found_files.setdefault(ext, []).append(full_path)

    # Print discovered file types
    print("Discovered file types:")
    discovered_filetypes = [ext for ext in EXTENSIONS if ext in matched_files or ext in found_files]
    for idx, ext in enumerate(discovered_filetypes, 1):
        print(f"{idx}. {ext.upper()} - Total: {len(matched_files.get(ext, [])) + len(found_files.get(ext, []))}")

    # Allow user to select which file types to display
    selection = input("\nEnter numbers of file types to display details for (comma-separated, 'all' for all, or 'skip' to skip): ").strip()
    if selection == "skip":
        sys.exit()
    elif selection == "all":
        selected_extensions = discovered_filetypes
    else:
        selected_indices = [int(s) for s in selection.split(',')]
        selected_extensions = [discovered_filetypes[i-1] for i in selected_indices]

    for ext in selected_extensions:
        if ext in matched_files:
            print(f"\n{GREEN}MATCHED {ext.upper()}: {len(matched_files[ext])}{RESET}")
            for f in matched_files[ext]:
                size = os.path.getsize(f)
                if size > 1024:
                    size = size / 1024.0
                    unit = "kb"
                else:
                    unit = "bytes"
                print(f"{f} - {size:.1f} {unit}")
        if ext in found_files:
            print(f"\n{BLUE}FOUND {ext.upper()}: {len(found_files[ext])}{RESET}")
            for f in found_files[ext]:
                size = os.path.getsize(f)
                if size > 1024:
                    size = size / 1024.0
                    unit = "kb"
                else:
                    unit = "bytes"
                print(f"{f} - {size:.1f} {unit}")

    if spwd_files:
        print("\nThe following files were found containing the case-insensitive string 'sPwd':")
        for f, lines in spwd_files:
            print(f"{GREEN}{f}{RESET}")
            for line in lines:
                colored_line = line.replace('spwd', f'{GREEN}sPwd{RESET}')
                print(f"    {colored_line}")
    else:
        print("\nNo files were found containing the case-insensitive string 'sPwd'.")

if __name__ == "__main__":
    main()

