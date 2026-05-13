# Action Item Extractor

一个基于 FastAPI + SQLite 的行动项提取应用，支持从自由格式的笔记中自动识别和提取可执行的任务清单。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)

---

## 项目概述

Action Item Extractor 能够从用户的自由格式笔记中智能提取行动项（action items）。应用提供两种提取模式：

| 提取方式 | 说明 |
|---------|------|
| **规则匹配** | 基于预定义模式（列表符号、TODO 标记、祈使句等）进行快速提取 |
| **LLM 驱动** | 使用 Ollama 大语言模型进行语义理解，适合复杂文本 |

### 核心功能

- 笔记的创建、读取、删除（CRUD）
- 行动项的批量提取与管理
- 行动项完成状态标记
- 可爱的 Web 交互界面

---

## 项目结构

```
week2/
├── app/
│   ├── main.py              # FastAPI 入口，注册路由，应用生命周期管理
│   ├── db.py                # SQLite 数据库操作层
│   ├── schemas.py            # Pydantic 数据模型定义
│   ├── routers/
│   │   ├── notes.py          # 笔记 CRUD 接口
│   │   └── action_items.py   # 行动项提取接口
│   └── services/
│       └── extract.py        # 行动项提取逻辑（规则 + LLM）
├── frontend/
│   └── index.html            # Web 界面（可爱风格）
├── tests/
│   └── test_extract.py       # 单元测试套件
├── data/                     # SQLite 数据库文件目录
├── class/
│   ├── simple_mcp.py         # MCP 服务器实现
│   └── coding_agent_from_scratch_lecture.py  # AI Coding Agent 示例
├── assignment.md             # 作业说明文档
└── writeup.md               # 作业报告
```

---

## 快速开始

### 环境要求

- Python 3.11+
- conda 或 venv 虚拟环境
- （可选）Ollama（用于 LLM 驱动提取）

### 安装与运行

```bash
# 1. 克隆项目后，进入项目目录
cd week2

# 2. 激活 conda 环境
conda activate cs146s

# 3. 安装依赖（使用 poetry）
poetry install

# 4. 启动开发服务器
poetry run uvicorn week2.app.main:app --reload
```

### 访问应用

启动后，在浏览器中打开：

```
http://127.0.0.1:8000/
```

### Ollama 配置（可选）

如需使用 LLM 驱动的提取功能，需先安装并启动 Ollama：

```bash
# 安装 Ollama（macOS/Linux）
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型（推荐使用轻量级模型）
ollama pull mistral-nemo:12b

# 启动 Ollama 服务
ollama serve
```

---

## API 端点

### 通用端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | Web 主界面 |
| `GET` | `/health` | 健康检查 |

### 笔记接口（Notes）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/notes` | 创建新笔记 |
| `GET` | `/notes` | 列出所有笔记 |
| `GET` | `/notes/{note_id}` | 获取指定笔记 |
| `DELETE` | `/notes/{note_id}` | 删除指定笔记 |

**创建笔记示例：**

```bash
curl -X POST "http://localhost:8000/notes" \
  -H "Content-Type: application/json" \
  -d '{"content": "今天需要完成：\n- 写代码\n- 做测试\n- 更新文档"}'
```

### 行动项接口（Action Items）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/action-items/extract` | 规则提取行动项 |
| `POST` | `/action-items/extract-llm` | LLM 提取行动项 |
| `GET` | `/action-items` | 列出所有行动项 |
| `POST` | `/action-items/{id}/done` | 标记行动项完成 |

**提取行动项示例（规则匹配）：**

```bash
curl -X POST "http://localhost:8000/action-items/extract" \
  -H "Content-Type: application/json" \
  -d '{"text": "今天要做：\n- [ ] 买菜\n- [ ] 做饭\n- 洗碗", "save_note": true}'
```

**响应示例：**

```json
{
  "note_id": 1,
  "items": [
    {"id": 1, "text": "买菜"},
    {"id": 2, "text": "做饭"},
    {"id": 3, "text": "洗碗"}
  ]
}
```

**LLM 提取示例：**

```bash
curl -X POST "http://localhost:8000/action-items/extract-llm" \
  -H "Content-Type: application/json" \
  -d '{"text": "项目会议要点：需要修复登录 bug，更新 API 文档，设计新的用户界面。"}'
```

---

## 数据库

应用使用 SQLite 数据库，数据库文件位于 `data/app.db`。

### 数据表

**notes** - 存储原始笔记

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| content | TEXT | 笔记内容 |
| created_at | TEXT | 创建时间 |

**action_items** - 存储提取的行动项

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| note_id | INTEGER | 关联笔记 ID（可为空） |
| text | TEXT | 行动项内容 |
| done | INTEGER | 完成状态（0/1） |
| created_at | TEXT | 创建时间 |

---

## 提取规则

### 规则匹配模式

应用支持以下格式的行动项识别：

1. **列表符号**
   - `- item`
   - `* item`
   - `1. item`

2. **关键词前缀**
   - `todo: item`
   - `action: item`
   - `next: item`

3. **复选框标记**
   - `[ ] item`
   - `[todo] item`

4. **祈使句**（fallback 模式）
   - 以动词开头的句子（add, create, fix, update 等）

### LLM 提取

当启用 Ollama 时，应用使用 `mistral-nemo:12b` 模型进行语义理解提取。该模式能够识别更复杂的表达方式，适合从自然语言段落中提取行动项。

---

## 测试

### 运行测试

```bash
# 运行所有测试
poetry run pytest week2/tests/test_extract.py -v

# 运行特定测试
poetry run pytest week2/tests/test_extract.py::test_extract_bullets_and_checkboxes -v

# 生成覆盖率报告
poetry run pytest week2/tests/test_extract.py --cov=app --cov-report=term-missing
```

### 测试覆盖

| 测试用例 | 说明 |
|---------|------|
| `test_extract_bullets_and_checkboxes` | 测试列表符号和复选框提取 |
| `test_llm_extract_empty_input` | 测试空输入处理 |
| `test_llm_extract_whitespace_only` | 测试纯空白输入处理 |
| `test_llm_extract_bullet_list` | 测试子弹列表格式提取 |
| `test_llm_extract_keyword_prefix` | 测试关键词前缀提取 |
| `test_llm_extract_mixed_format` | 测试混合格式输入 |
| `test_llm_extract_json_with_markdown` | 测试 Markdown JSON 块解析 |
| `test_llm_extract_deduplication` | 测试去重功能 |
| `test_llm_extract_fallback_on_error` | 测试 LLM 错误时的降级处理 |
| `test_llm_extract_case_insensitive_dedup` | 测试大小写不敏感去重 |
| `test_llm_extract_returns_list` | 测试返回类型验证 |
| `test_llm_extract_handles_dict_format` | 测试字典格式 JSON 响应处理 |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 数据库 | SQLite |
| 数据验证 | Pydantic |
| LLM | Ollama (mistral-nemo:12b) |
| 测试 | pytest |
| 包管理 | Poetry |

---

## 开发说明

### 代码规范

- 使用类型注解（typing hints）
- Pydantic schemas 定义 API 契约
- 数据库层与业务逻辑分离
- 统一的异常处理

### 日志

应用使用 Python logging 模块，默认日志级别为 INFO。

```python
# 在应用代码中查看日志
logger.info("Extracting action items (rule-based)")
```

---

## 许可

本项目仅用于教育目的。
