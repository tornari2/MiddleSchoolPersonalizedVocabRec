#!/bin/bash
# Build script for Lambda layer with dependencies
# This script creates the lambda layer ZIP file with all required dependencies

set -e

echo "Building Lambda layer (with cached virtual environment)..."

# Determine script directory to be robust when invoked from elsewhere
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# Create or reuse cached virtual environment for dependencies
# ------------------------------------------------------------------------------
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment for caching..."
  python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Ensure pip is reasonably up-to-date (fast, local)
python -m pip install --upgrade pip >/dev/null 2>&1 || true

# Install or update dependencies only when requirements.txt changes
REQ_HASH_CURRENT="$(shasum -a 256 requirements.txt | awk '{print $1}')"
REQ_HASH_FILE="venv/.requirements.sha256"

if [ ! -f "$REQ_HASH_FILE" ]; then
  echo "Installing Python dependencies into cached venv (first-time)..."
  pip install -r requirements.txt
  echo "$REQ_HASH_CURRENT" > "$REQ_HASH_FILE"
else
  REQ_HASH_PREV="$(cat "$REQ_HASH_FILE")"
  if [ "$REQ_HASH_CURRENT" != "$REQ_HASH_PREV" ]; then
    echo "requirements.txt changed. Updating cached dependencies..."
    pip install -r requirements.txt
    echo "$REQ_HASH_CURRENT" > "$REQ_HASH_FILE"
  else
    echo "Cached dependencies are up to date. Skipping reinstall."
  fi
fi

# ------------------------------------------------------------------------------
# Prepare layer folder from cached site-packages + project modules/data
# ------------------------------------------------------------------------------
echo "Cleaning previous build artifacts..."
rm -rf python/
rm -f ../infrastructure/terraform/recommendation_layer.zip

# Create python directory for layer
mkdir -p python

# Copy dependencies from cached venv into layer
echo "Copying dependencies from cached virtual environment..."
# Support typical venv layout: venv/lib/pythonX.Y/site-packages
SITE_PACKAGES_PATH=$(python - <<'PY'
import sys,glob,os
base=os.path.join("venv","lib")
candidates=glob.glob(os.path.join(base,"python*","site-packages"))
print(candidates[0] if candidates else "")
PY
)

if [ -z "$SITE_PACKAGES_PATH" ]; then
  echo "Error: Could not locate site-packages in venv."
  exit 1
fi

cp -R "$SITE_PACKAGES_PATH/"* python/

# Clean up cache files to reduce size
echo "Cleaning up cache files..."
find python/lib/python*/site-packages/ -name "*.pyc" -delete 2>/dev/null || true
find python/lib/python*/site-packages/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
# Also clean top-level since we copied directly into python/
find python/ -name "*.pyc" -delete 2>/dev/null || true
find python/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy custom modules
echo "Copying custom modules..."
cp ../auth_utils.py python/
cp ../recommendation_engine.py python/
cp ../reference_data_loader.py python/
cp ../vocabulary_profiler.py python/
cp ../schema_validation.py python/
cp ../openai_service.py python/

# Copy reference data
echo "Copying reference data..."
mkdir -p python/reference_data/
cp ../reference_data/*.json python/reference_data/

# Create the layer ZIP file
echo "Creating layer ZIP file..."
cd python
zip -r ../recommendation_layer.zip .
cd ..

# Move to Terraform directory
mv recommendation_layer.zip ../infrastructure/terraform/

echo "Lambda layer built successfully!"
echo "Layer ZIP: ../infrastructure/terraform/recommendation_layer.zip"
