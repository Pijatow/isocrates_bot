#!/bin/bash

# --- Isocrates Bot Project Reset Script ---
echo "🧹 Starting project cleanup..."

# 1. Remove the 'logs' directory
if [ -d "logs" ]; then
  echo "🔥 Deleting log directory..."
  rm -rf logs
  echo "✅ Log directory deleted."
else
  echo "💨 Log directory not found, skipping."
fi

# 2. Remove Python cache directories
echo "🔥 Deleting Python cache directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +
echo "✅ Python cache deleted."

# 3. Remove the database file
if [ -f "isocrates.db" ]; then
  echo "🔥 Deleting database file..."
  rm -f isocrates.db
  echo "✅ Database file deleted."
else
  echo "💨 Database file not found, skipping."
fi

echo "✨ Project cleanup complete. ✨"
