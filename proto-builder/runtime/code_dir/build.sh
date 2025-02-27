#!/bin/bash
set -e

# Build the React app
cd frontend
npm install
npm run build

# Ensure backend/static exists and copy the build output
cd ..
mkdir -p backend/static
cp -r frontend/build/* backend/static/

echo "React app built and copied to backend/static."
