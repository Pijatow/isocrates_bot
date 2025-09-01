#!/bin/bash

# --- Isocrates Bot Project Reset Script ---
# This script cleans the project by removing temporary files and directories.
# It should be run from the root of the project repository.
# To make it executable, run: chmod +x reset_project.sh

echo "🧹 Starting project cleanup..."

# 1. Remove the entire 'logs' directory
if [ -d "logs" ]; then
  echo "🔥 Deleting log directory..."
  rm -rf logs
  echo "✅ Log directory deleted."
else
  echo "💨 Log directory not found, skipping."
fi

# 2. Remove all '__pycache__' directories
# This command finds all directories named '__pycache__' and removes them.
echo "🔥 Deleting Python cache directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +
echo "✅ Python cache deleted."

# --- Future additions can go here ---
# For example, when we add a database:
# echo "🔥 Deleting database file..."
# rm -f isocrates.db
# echo "✅ Database file deleted."

echo "✨ Project cleanup complete. Environment is fresh and clean! ✨"
