---
name: llamafs-organizer
description: 智能文件整理工具。
---

# LlamaFS 智能文件整理工具

## 项目信息

| 项目 | 路径/地址 |
|------|----------|
| 项目目录 | `~/llama-fs` |
| 虚拟环境 | `~/llama-fs/venv` |
| 配置文件 | `~/llama-fs/.env` |
| 你的 Fork | https://github.com/cosyeezz/llama-fs |
| 上游仓库 | https://github.com/iyaja/llama-fs |

---

## ⚠️ 核心规则（必须遵守）

### 规则 1：所有 curl 请求必须绕过代理

```bash
curl --noproxy '*' -s ...
```

### 规则 2：服务自动启动（强制执行）

**在执行操作 1、2、5 之前，必须先运行以下脚本。不询问用户，直接执行。无论任何情况都不要询问用户是否启动服务。**

```bash
# === 服务自动启动脚本 - 作为单个 bash 命令执行，设置 timeout=60000 ===
# Step 1: 检查服务是否正常响应
SERVICE_STATUS=$(curl --noproxy '*' -s --connect-timeout 3 -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
if [ "$SERVICE_STATUS" != "000" ]; then
  echo "✓ 服务已在运行"
else
  # Step 2: 清理占用 8000 端口的孤儿/僵尸进程
  ZOMBIE_PID=$(lsof -ti :8000 2>/dev/null)
  if [ -n "$ZOMBIE_PID" ]; then
    echo "发现端口 8000 被占用 (PID: $ZOMBIE_PID)，正在清理..."
    kill -9 $ZOMBIE_PID 2>/dev/null; sleep 1
  fi
  # Step 3: 启动服务
  echo "正在启动服务..."
  cd ~/llama-fs && source venv/bin/activate && nohup fastapi dev server.py > /tmp/llamafs.log 2>&1 &
  # Step 4: 等待服务就绪
  for i in {1..30}; do
    sleep 1
    CHECK=$(curl --noproxy '*' -s --connect-timeout 2 -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
    if [ "$CHECK" != "000" ]; then echo "✓ 服务已启动"; break; fi
    if [ $i -eq 30 ]; then echo "✗ 启动超时，查看日志:"; tail -20 /tmp/llamafs.log; fi
  done
fi
```

**⚠️ 执行要求**：
- 必须设置 `timeout=60000`（60秒），因为启动需要时间
- 必须添加 `--connect-timeout 3` 到 curl 命令，避免无限等待
- **绝对禁止询问用户**：如果服务没启动，直接启动，不要问
---

## 操作手册

### 🚀 操作 1：启动服务

**触发词**: "启动文件整理服务"、"启动 llamafs"、"start llamafs"

**执行**: 直接运行上面的「服务自动启动脚本」

**完成后**: 告知用户 "服务已启动，运行在 http://127.0.0.1:8000"

---

### 📁 操作 2：整理文件夹

**触发词**: "整理文件"、"整理下载文件夹"、"整理桌面"、"文件太乱了"、"清理文件夹"、"整理当前文件夹"

**步骤**:

**Step 1** - 运行「服务自动启动脚本」（不询问用户）

**Step 2** - 确定目标文件夹:
- 用户说"下载文件夹" → `/Users/dane/Downloads/`
- 用户说"桌面" → `/Users/dane/Desktop/`
- 用户说"当前文件夹" → 使用当前工作目录
- 用户指定路径 → 使用用户指定的路径
- 未指定 → 询问用户要整理哪个文件夹

**Step 3** - 调用 AI 分析（设置 bash timeout=120000，AI 分析耗时较长）:
```bash
curl --noproxy '*' -s --max-time 90 -X POST http://127.0.0.1:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"path": "<目标文件夹路径>"}'
```

**Step 4** - 展示建议方案（表格格式）:

| 原文件 | 建议位置 | AI 分析 |
|--------|----------|---------|
| src_path | dst_path | summary |

**Step 5** - 询问确认:
"以上是 AI 建议的整理方案。要执行吗？你也可以说「只移动图片」或「跳过某个文件」。"

**Step 6** - 执行移动:
```bash
curl --noproxy '*' -s -X POST http://127.0.0.1:8000/commit \
  -H "Content-Type: application/json" \
  -d '{"base_path": "<文件夹>", "src_path": "<原路径>", "dst_path": "<新路径>"}'
```

**Step 7** - 报告: "整理完成！共移动了 X 个文件。"

---

### 🔄 操作 3：同步上游更新

**触发词**: "同步 llamafs"、"更新 llamafs 代码"、"sync llamafs"

**执行**:
```bash
cd ~/llama-fs && git fetch upstream && git merge upstream/main -m "chore: sync with upstream" && git push origin main
```

---

### 📦 操作 4：更新依赖

**触发词**: "更新 llamafs 依赖"、"upgrade llamafs dependencies"

**执行**:
```bash
cd ~/llama-fs && source venv/bin/activate && pip install --proxy=http://127.0.0.1:10808 -r requirements.txt --upgrade 2>&1 | tail -10
```

---

### ❓ 操作 5：检查状态

**触发词**: "llamafs 状态"、"检查文件整理服务"、"llamafs status"

**执行**: 先运行「服务自动启动脚本」，然后：
```bash
# 检查 git 状态
cd ~/llama-fs && git status --short

# 检查配置
cat ~/llama-fs/.env | grep -v "^#" | grep -v "^$"
```

---

### ⚙️ 操作 6：修改配置

**触发词**: "修改 llamafs 配置"、"更换 API key"、"修改 API 地址"

**配置文件**: `~/llama-fs/.env`

**可配置项**:
- `OPENAI_API_KEY` - API 密钥
- `OPENAI_BASE_URL` - API 地址
- `OPENAI_MODEL` - 模型名称（默认 `claude-haiku-4-5-20251001`）

---

### 🛑 操作 7：停止服务

**触发词**: "停止 llamafs"、"关闭文件整理服务"、"stop llamafs"

**执行**:
```bash
pkill -f "fastapi dev server.py" && echo "服务已停止" || echo "服务未在运行"
```

---

## 支持的文件类型

| 类型 | 扩展名 | AI 如何处理 |
|------|--------|------------|
| 图片 | .png, .jpg, .jpeg | 视觉模型分析图片内容，生成描述性文件名 |
| PDF | .pdf | 提取文本内容，按主题分类 |
| 文本 | .txt | 读取内容，按主题分类 |
| 其他 | * | 按文件名和扩展名智能分类 |

## 典型对话示例

| 用户说 | 执行 |
|--------|------|
| "我的下载文件夹太乱了" | 操作 2，目标 = ~/Downloads/ |
| "启动文件整理服务" | 操作 1 |
| "帮我整理一下桌面" | 操作 2，目标 = ~/Desktop/ |
| "整理当前文件夹" | 操作 2，目标 = 当前工作目录 |
| "同步一下 llamafs" | 操作 3 |
| "llamafs 什么状态" | 操作 5 |
| "停止 llamafs" | 操作 7 |
