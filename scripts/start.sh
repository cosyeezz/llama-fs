#!/bin/bash
# 启动 LlamaFS 服务
cd "$(dirname "$0")/.."

# 激活虚拟环境
source venv/bin/activate

# 检查 .env
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it first."
    echo "   cp .env.example .env"
    exit 1
fi

echo "🚀 Starting LlamaFS server..."
echo "   API: http://127.0.0.1:8000"
echo "   Docs: http://127.0.0.1:8000/docs"
echo ""

fastapi dev server.py
