---
name: llamafs-organizer
description: AI 智能文件整理工具。当用户提到"整理文件"、"清理下载文件夹"、"整理桌面"、"文件太乱了"、"organize files"、"clean up downloads"、"整理混乱的文件夹"、"启动文件整理服务"、"启动 llamafs"、"同步 llamafs"、"更新 llamafs"、"llamafs 状态"时必须触发此技能。这是一个完整的文件整理解决方案，所有操作都通过此 skill 完成。
---

# LlamaFS 智能文件整理工具

这是一个完整的 AI 文件整理解决方案。所有操作（启动服务、整理文件、同步更新、维护）都通过此 skill 完成。

## 项目信息

| 项目 | 路径/地址 |
|------|----------|
| 项目目录 | `~/llama-fs` |
| 虚拟环境 | `~/llama-fs/venv` |
| 配置文件 | `~/llama-fs/.env` |
| 你的 Fork | https://github.com/cosyeezz/llama-fs |
| 上游仓库 | https://github.com/iyaja/llama-fs |

---

## ⚠️ 重要：网络请求规则

**所有 curl 请求必须绕过代理**，使用 `--noproxy '*'` 参数：
```bash
curl --noproxy '*' -s ...
```

---

## 🔧 服务自动管理（内部使用）

**在执行任何需要服务的操作前，必须先运行此检查流程：**

### 自动启动流程

```bash
# Step 1: 检查服务是否运行
SERVICE_STATUS=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")

# Step 2: 如果服务未运行 (状态码为 000)，自动启动
if [ "$SERVICE_STATUS" = "000" ]; then
  # 后台启动服务，输出重定向到日志
  cd ~/llama-fs && source venv/bin/activate && nohup fastapi dev server.py > /tmp/llamafs.log 2>&1 &
  
  # 等待服务启动（最多 30 秒）
  for i in {1..30}; do
    sleep 1
    if curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null | grep -q "200\|404"; then
      echo "服务已启动"
      break
    fi
    if [ $i -eq 30 ]; then
      echo "服务启动超时，请检查日志: /tmp/llamafs.log"
      exit 1
    fi
  done
fi
```

**注意**: 此流程由 AI 自动执行，用户无需手动操作。

---

## 操作手册

根据用户意图选择对应操作执行。

### 🚀 操作 1：启动服务

**触发词**: "启动文件整理服务"、"启动 llamafs"、"start llamafs"

**执行**:
```bash
# 先检查是否已运行
SERVICE_STATUS=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")

if [ "$SERVICE_STATUS" != "000" ]; then
  echo "服务已在运行中"
else
  cd ~/llama-fs && source venv/bin/activate && nohup fastapi dev server.py > /tmp/llamafs.log 2>&1 &
  sleep 3
  echo "服务启动中，日志位于 /tmp/llamafs.log"
fi
```

**完成后告知用户**: "服务已启动，运行在 http://127.0.0.1:8000。"

---

### 📁 操作 2：整理文件夹

**触发词**: "整理文件"、"整理下载文件夹"、"整理桌面"、"文件太乱了"、"清理文件夹"、"整理当前文件夹"

**步骤**:

**Step 1** - 自动确保服务运行（不询问用户）:
```bash
# 检查并自动启动服务
SERVICE_STATUS=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")

if [ "$SERVICE_STATUS" = "000" ]; then
  echo "正在自动启动服务..."
  cd ~/llama-fs && source venv/bin/activate && nohup fastapi dev server.py > /tmp/llamafs.log 2>&1 &
  
  # 等待服务就绪
  for i in {1..30}; do
    sleep 1
    CHECK=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
    if [ "$CHECK" != "000" ]; then
      echo "服务已就绪"
      break
    fi
    if [ $i -eq 30 ]; then
      echo "ERROR: 服务启动超时"
      cat /tmp/llamafs.log | tail -20
      exit 1
    fi
  done
fi
```

**Step 2** - 确定目标文件夹:
- 用户说"下载文件夹" → `/Users/dane/Downloads/`
- 用户说"桌面" → `/Users/dane/Desktop/`
- 用户说"当前文件夹" → 使用当前工作目录 (通过 `pwd` 获取)
- 用户指定路径 → 使用用户指定的路径
- 未指定 → 询问用户要整理哪个文件夹

**Step 3** - 调用 AI 分析:
```bash
curl --noproxy '*' -s -X POST http://127.0.0.1:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"path": "<目标文件夹路径>"}'
```

**Step 4** - 展示建议方案:
将返回的 JSON 格式化为表格展示给用户：

| 原文件 | 建议位置 | AI 分析 |
|--------|----------|---------|
| src_path | dst_path | summary |

**Step 5** - 询问确认:
"以上是 AI 建议的整理方案。要执行吗？你也可以说「只移动图片」或「跳过某个文件」。"

**Step 6** - 执行移动:
对用户确认的每个文件调用:
```bash
curl --noproxy '*' -s -X POST http://127.0.0.1:8000/commit \
  -H "Content-Type: application/json" \
  -d '{"base_path": "<文件夹>", "src_path": "<原路径>", "dst_path": "<新路径>"}'
```

**Step 7** - 报告结果:
"整理完成！共移动了 X 个文件。"

---

### 🔄 操作 3：同步上游更新

**触发词**: "同步 llamafs"、"更新 llamafs 代码"、"sync llamafs"

**执行**:
```bash
cd ~/llama-fs && git fetch upstream && git merge upstream/main -m "chore: sync with upstream" && git push origin main
```

**可能的结果**:
- 成功 → "已同步上游最新代码并推送到你的 fork。"
- 冲突 → 报告冲突文件，询问用户如何处理

---

### 📦 操作 4：更新依赖

**触发词**: "更新 llamafs 依赖"、"upgrade llamafs dependencies"

**执行**:
```bash
cd ~/llama-fs && source venv/bin/activate && pip install --proxy=http://127.0.0.1:10808 -r requirements.txt --upgrade 2>&1 | tail -10
```

**完成后**: "依赖已更新到最新版本。"

---

### ❓ 操作 5：检查状态

**触发词**: "llamafs 状态"、"检查文件整理服务"、"llamafs status"

**执行**:
```bash
# 检查服务
SERVICE_STATUS=$(curl --noproxy '*' -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
if [ "$SERVICE_STATUS" = "000" ]; then
  echo "服务状态: 未运行"
else
  echo "服务状态: 运行中 (HTTP $SERVICE_STATUS)"
fi

# 检查 git 状态
cd ~/llama-fs && git status --short

# 检查配置
cat ~/llama-fs/.env | grep -v "^#" | grep -v "^$"
```

**展示**: 服务状态、代码状态、配置信息

---

### ⚙️ 操作 6：修改配置

**触发词**: "修改 llamafs 配置"、"更换 API key"、"修改 API 地址"

**配置文件**: `~/llama-fs/.env`

**可配置项**:
- `OPENAI_API_KEY` - API 密钥
- `OPENAI_BASE_URL` - API 地址（支持第三方代理）
- `OPENAI_MODEL` - 模型名称（默认 `claude-haiku-4-5-20251001`，可换成其他兼容 OpenAI API 的模型）

**执行**: 使用 edit 工具修改 `~/llama-fs/.env`

---

### 🛑 操作 7：停止服务

**触发词**: "停止 llamafs"、"关闭文件整理服务"、"stop llamafs"

**执行**:
```bash
# 查找并终止 fastapi 进程
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

**用户**: "我的下载文件夹太乱了"
**执行**: 操作 2（整理文件夹），目标 = ~/Downloads/（自动启动服务如需要）

**用户**: "启动文件整理服务"
**执行**: 操作 1（启动服务）

**用户**: "帮我整理一下桌面"
**执行**: 操作 2（整理文件夹），目标 = ~/Desktop/（自动启动服务如需要）

**用户**: "整理当前文件夹"
**执行**: 操作 2（整理文件夹），目标 = 当前工作目录（自动启动服务如需要）

**用户**: "同步一下 llamafs"
**执行**: 操作 3（同步上游更新）

**用户**: "llamafs 什么状态"
**执行**: 操作 5（检查状态）

**用户**: "停止 llamafs"
**执行**: 操作 7（停止服务）
