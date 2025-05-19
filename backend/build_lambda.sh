#!/bin/bash

set -e
set -u

BUILD_DIR="lambda_build"
ZIP_NAME="lambda-pkg.zip"
SRC_DIRS=("main.py" "routes" "services")
REQUIREMENTS="requirements.txt"

# Helper for error handling
error_exit() {
    echo "Error: $1"
    exit 1
}

# Cleanup
echo "Cleaning previous build, if any..."
rm -rf "$BUILD_DIR" "$ZIP_NAME" || error_exit "ERROR: Failed to remove old build directory or zip."
mkdir -p "$BUILD_DIR" || error_exit "ERROR: Failed to create build directory."

# Install dependencies
if [[ ! -f "$REQUIREMENTS" ]]; then
    error_exit "ERROR: requirements.txt not found"
fi

echo "Installing dependencies from $REQUIREMENTS..."
pip install -r "$REQUIREMENTS" -t "$BUILD_DIR" || error_exit "ERROR: Failed to install dependencies."

# Copy source files into the build directory
echo "Copying source files..."
for item in "${SRC_DIRS[@]}"; do
    if [[ -e "$item" ]]; then
        cp -r "$item" "$BUILD_DIR/" || error_exit "ERROR: Failed to copy $item"
    else
        error_exit "ERROR: Source item $item does not exist."
    fi
done

# Zippery
echo "Creating zip file..."
cd "$BUILD_DIR" || error_exit "ERROR: Failed to enter build directory."
zip -r "../$ZIP_NAME" . || error_exit "ERROR: Failed to zip deployment package."
cd ..

echo "$ZIP_NAME created successfully in $(pwd)."