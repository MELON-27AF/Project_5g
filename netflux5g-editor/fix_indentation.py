#!/usr/bin/env python3
"""
Quick fix for the indentation error in mininet_export.py
"""

import re
from pathlib import Path

def fix_indentation_error():
    """Fix the indentation error in mininet_export.py"""
    
    file_path = Path(__file__).parent / "src" / "export" / "mininet_export.py"
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False
    
    print(f"🔧 Fixing indentation in {file_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and fix the problematic lines
    fixed_lines = []
    in_sanitize_function = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check if we're in the sanitize_variable_name function
        if 'def sanitize_variable_name(self, name):' in line:
            in_sanitize_function = True
            fixed_lines.append(line)
            continue
        
        # Check if we've exited the function
        if in_sanitize_function and line.strip().startswith('def ') and 'sanitize_variable_name' not in line:
            in_sanitize_function = False
        
        # Fix indentation issues in the sanitize function
        if in_sanitize_function and line_num >= 1325 and line_num <= 1335:
            # Ensure proper indentation for function content
            stripped = line.lstrip()
            if stripped and not stripped.startswith('"""') and not stripped.startswith('#'):
                # This should be indented as function content (8 spaces)
                if stripped.startswith('import ') or stripped.startswith('clean_name') or stripped.startswith('if ') or stripped.startswith('return '):
                    line = '        ' + stripped
                elif stripped.startswith('#'):
                    line = '        ' + stripped
            elif stripped.startswith('#'):
                # Comments should be indented as function content
                line = '        ' + stripped
        
        fixed_lines.append(line)
    
    # Write the fixed content back
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        print("✅ Fixed indentation issues")
        return True
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False

def test_syntax():
    """Test if the file has valid Python syntax"""
    import subprocess
    
    file_path = Path(__file__).parent / "src" / "export" / "mininet_export.py"
    
    try:
        result = subprocess.run(
            ['python3', '-m', 'py_compile', str(file_path)],
            capture_output=True, text=True, cwd=file_path.parent.parent
        )
        
        if result.returncode == 0:
            print("✅ Syntax check passed")
            return True
        else:
            print(f"❌ Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running syntax check: {e}")
        return False

def main():
    """Main function"""
    print("🔧 NetFlux5G Indentation Fix")
    print("=" * 30)
    
    if fix_indentation_error():
        if test_syntax():
            print("\n🎉 Fix completed successfully!")
            print("You can now run: python3 src/main.py")
        else:
            print("\n⚠️  File fixed but still has syntax issues.")
            print("Manual review may be needed.")
    else:
        print("\n❌ Fix failed. Manual intervention required.")

if __name__ == "__main__":
    main()
