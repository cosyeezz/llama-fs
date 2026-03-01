#!/bin/bash
# 整理指定文件夹
# 用法: ./scripts/organize.sh /path/to/folder

FOLDER="${1:-$HOME/Downloads}"

if [ ! -d "$FOLDER" ]; then
    echo "❌ Folder not found: $FOLDER"
    exit 1
fi

echo "📁 Organizing: $FOLDER"
echo ""

# 调用 API
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/batch \
    -H "Content-Type: application/json" \
    -d "{\"path\": \"$FOLDER\"}")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

echo ""
echo "💡 To apply changes, use the /commit endpoint for each file."
