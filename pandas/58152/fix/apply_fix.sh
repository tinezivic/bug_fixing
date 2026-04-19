#!/bin/bash
# Apply the fix to a pandas source checkout
# Usage: ./apply_fix.sh /path/to/pandas-src

set -e

PANDAS_DIR="${1:-$(dirname "$0")/../pandas-src}"

if [ ! -f "$PANDAS_DIR/pandas/core/arrays/arrow/array.py" ]; then
    echo "Error: pandas source not found at $PANDAS_DIR"
    echo "Usage: $0 /path/to/pandas-src"
    exit 1
fi

cd "$PANDAS_DIR"
git apply "$(dirname "$0")/array.py.patch"
echo "Patch applied successfully."
