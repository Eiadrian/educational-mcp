## AI 教学智能体

- LLM 负责理解自然语言与决策；所有“教育小模型”通过 FastAPI 暴露，接口统一。
- 状态（掌握度/情绪/作答历史）用轻量内存存储演示，后续可替换数据库（SQLAlchemy 等）。

### 目录结构

```
main.py            # FastAPI 入口，挂载所有路由
schemas.py         # Pydantic 数据模型（请求/响应）
database.py        # 轻量内存“数据库”（可换持久化）
models/            # 小模型业务逻辑（可换训练模型）
  cognitive_diagnosis.py
  knowledge_tracking.py
  emotion_analysis.py
  path_planning.py
routers/           # FastAPI 路由拆分
  cognitive.py
  tracking.py
  emotion.py
  planning.py
```

### 接口一览

- `POST /diagnose`：认知诊断（规则占位，可换 CDM/IRT）。
- `POST /track`：知识追踪（规则占位，可换 DKVMN/AKT）。
- `POST /emotion`，`/emotion/sentiment`：情感状态与文本情感。
- `POST /plan`：路径规划。

所有请求支持 `request_id`；响应带 `mode/model_version`，标注实现可靠度。

### 启动

```bash
pip install -r requirements.txt
python main.py
```

默认监听 `http://127.0.0.1:8000`，访问 `/docs` 可在线调试。LLM 侧可直接把这些 HTTP 路由注册为 MCP 工具。

### 演进建议

- 用持久化数据库替换 `database.py`，保留同名接口即可平滑升级。
- 将 `models/*` 内的规则逻辑替换为训练模型；对外 schema 不变。
