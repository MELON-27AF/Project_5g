#!/bin/bash
# Quick fix for indentation issue in mininet_export.py

echo "🔧 Fixing indentation issue in mininet_export.py"

cd "$(dirname "$0")/src/export"

# Create a backup
cp mininet_export.py mininet_export.py.backup

# Fix the indentation around lines 1325-1340
# The issue appears to be with the sanitize_variable_name function
python3 << 'EOF'
import re

# Read the file
with open('mininet_export.py', 'r') as f:
    content = f.read()

# Split into lines
lines = content.split('\n')

# Fix the specific problematic area around sanitize_variable_name function
for i in range(len(lines)):
    line = lines[i]
    line_num = i + 1
    
    # Fix indentation for lines in the sanitize_variable_name function
    if line_num >= 1324 and line_num <= 1332:
        stripped = line.lstrip()
        if stripped:
            if ('import re' in stripped or 
                'clean_name =' in stripped or 
                'if clean_name' in stripped or 
                'return clean_name' in stripped or 
                stripped.startswith('# Remove special')):
                # These should be indented with 8 spaces (function body)
                lines[i] = '        ' + stripped

# Write back the fixed content
with open('mininet_export.py', 'w') as f:
    f.write('\n'.join(lines))

print("✅ Fixed indentation")
EOF

# Test the syntax
echo "🧪 Testing syntax..."
python3 -m py_compile mininet_export.py

if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed!"
    echo "You can now run: python3 ../main.py"
else
    echo "❌ Still has syntax issues. Restoring backup..."
    mv mininet_export.py.backup mininet_export.py
fi
