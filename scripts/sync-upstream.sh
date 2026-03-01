#!/bin/bash
# 同步上游更新
cd "$(dirname "$0")/.."

echo "📥 Fetching upstream..."
git fetch upstream

echo "🔀 Merging upstream/main..."
git merge upstream/main -m "chore: sync with upstream"

if [ $? -eq 0 ]; then
    echo "✅ Sync successful!"
    echo "📤 Pushing to origin..."
    git push origin main
else
    echo "⚠️  Merge conflict detected. Please resolve manually."
    exit 1
fi
