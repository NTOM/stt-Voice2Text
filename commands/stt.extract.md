---
description: 从音频/视频文件提取 JSON 转录结果，支持所有常见格式（wav/mp3/mp4/flac/ogg 等），服务端自动转换。
arguments:
  - name: audio-file-path
    description: 音频/视频文件路径（相对或绝对），支持 wav、mp3、mp4、flac、ogg、m4a、aac、wma、webm 等格式
    required: true
  - name: model
    description: 使用的 whisper 模型名称（如 tiny / base / small / medium / large-v3）
    required: false
---

## User Input

```text
$ARGUMENTS
```

你 **必须** 在执行前考虑用户输入（如果非空）。

## Operating Constraints

- **文件写入范围**：仅允许写入 `Export/` 目录下的 `.json` 文件
- **幂等性保证**：重复执行同一输入覆盖已有 JSON 文件
- **服务依赖**：依赖本地 stt 服务 `http://127.0.0.1:9977`
- **错误即停**：任何步骤失败必须立即报告并停止，不得静默跳过
- **上游隔离**：不修改 `start.py` 和任何上游文件

## Outline

### 1. 输入验证

1. 检查 `{{audio-file-path}}` 是否为非空字符串
   - 为空 → 提示用户提供音频文件路径，**ABORT**
2. 检查文件是否存在
   - 不存在 → 提示用户检查路径，**ABORT**
3. 检查文件扩展名是否为支持的音频/视频格式
   - 支持的扩展名：`.wav`、`.mp3`、`.mp4`、`.flac`、`.ogg`、`.m4a`、`.aac`、`.wma`、`.webm`、`.avi`、`.mkv`、`.mov`
   - 不在支持列表中 → 提示：不支持的文件格式 `{ext}`，请使用以上支持的音频/视频格式。**ABORT**
   > 说明：stt 服务内置 FFmpeg，会自动将所有格式转换为 16kHz 单声道 wav 后再进行识别，用户无需手动转换。
4. 检查文件大小
   - 超过 500MB → 提示文件过大，建议分段处理或通过 Web UI 上传。**ABORT**

记录音频文件路径为 `AUDIO_PATH`，提取文件名（不含扩展名）为 `STEM`。

### 1.5. 模型选择

**如果用户已通过参数指定 `{{model}}`**（非空），直接使用该值作为 `MODEL`。

**如果用户未指定模型**，向用户展示以下模型列表并请求选择：

```
请选择要使用的 whisper 模型：

| # | 模型 | 大小 | 精度 | 资源需求 | 说明 |
|---|------|------|------|----------|------|
| 1 | tiny | ~75 MB | ★☆☆☆☆ | 极低 | 速度最快，精度最低 |
| 2 | base | ~145 MB | ★★☆☆☆ | 低 | 轻量推荐 |
| 3 | small | ~484 MB | ★★★☆☆ | 中 | 均衡之选 |
| 4 | medium | ~1.5 GB | ★★★★☆ | 较高 | 高精度 |
| 5 | large-v3 | ~3 GB | ★★★★★ | 高 | 最高精度（建议 CUDA） |

💡 不确定选哪个？推荐 base（快速）或 small（均衡）。
```

等待用户输入编号或模型名称，记录为 `MODEL`。

- 输入 `1`~`5` → 映射为对应模型名
- 输入有效模型名（如 `small`）→ 直接使用
- 输入无效 → 提示重新选择

### 2. 服务检测与自动启动

**检测服务状态**：

在终端执行 HTTP 请求检测 stt 服务是否可达：

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:9977" -Method GET -TimeoutSec 5 -UseBasicParsing
```

或使用 curl（如果可用）：

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9977 --connect-timeout 5
```

**判定逻辑**：

| 结果 | 动作 |
|------|------|
| HTTP 200 或任意 HTTP 响应 | ✅ 服务已运行，跳到 Step 3 |
| 连接失败 / 超时 | ⚠️ 服务未运行，执行自动启动 |

**自动启动流程**（仅在服务未运行时执行）：

1. 提示用户：
   ```
   ℹ️ stt 服务未运行，正在自动启动...
   ```

2. 在终端执行启动命令：
   ```bash
   python start.py
   ```
   > 注意：`start.py` 会阻塞终端（Flask 服务），需要在后台或新终端中运行。

3. **轮询等待服务就绪**：
   - 间隔：5 秒
   - 最大等待：60 秒（共 12 次轮询）
   - 每次轮询执行 HTTP GET `http://127.0.0.1:9977`
   - 收到 HTTP 响应 → 服务就绪，继续 Step 3

4. **超时或启动失败时降级处理**：

   如果 60 秒内服务未就绪，**ABORT** 并输出诊断信息：

   ```
   ❌ stt 服务启动超时（60 秒）

   可能的原因及修复步骤：
   1. 缺少依赖 → 运行 `pip install -r requirements.txt`
   2. 端口 9977 被占用 → 运行 `netstat -ano | findstr :9977` 检查占用进程
   3. 模型文件缺失 → 检查 `models/` 目录是否包含所需模型
   4. 手动启动 → 在新终端中运行 `python start.py`，观察错误日志
   ```

### 3. API 调用提取转录结果

**确认 `Export/` 目录存在**：

```bash
mkdir -p Export
```

或 PowerShell：

```powershell
New-Item -ItemType Directory -Path "Export" -Force | Out-Null
```

**调用 stt API**：

首选端点 `/api`，使用 multipart/form-data 提交音频文件，**必须指定 `model` 和 `response_format`**：

```bash
curl -X POST "http://127.0.0.1:9977/api" \
  -F "file=@{{AUDIO_PATH}}" \
  -F "model={{MODEL}}" \
  -F "response_format=json" \
  -o "Export/{{STEM}}.json"
```

或 PowerShell：

```powershell
$formData = @{
    file = Get-Item "{{AUDIO_PATH}}"
    model = "{{MODEL}}"
    response_format = "json"
}
$response = Invoke-RestMethod -Uri "http://127.0.0.1:9977/api" -Method POST -Form $formData
```

> 备选端点：如果 `/api` 返回错误，尝试 `/v1/audio/transcriptions`。

**错误处理**：
- API 返回非 200 状态码 → 显示错误详情，**ABORT**
- 返回内容为空或非 JSON → 提示 API 响应异常，**ABORT**
- 网络超时 → 提示检查服务状态，**ABORT**

### 4. 保存结果并验证

1. 将 JSON 结果保存到 `Export/{STEM}.json`
2. 验证保存的文件：
   - 文件存在且非空
   - 内容为有效 JSON
   - 包含预期的转录字段（`line`、`start_time`、`end_time`、`text`）

### 5. 完成报告

**完成报告**：

```
✅ 音频转录提取完成

| 指标 | 值 |
|------|-----|
| 音频文件 | {AUDIO_PATH} |
| 使用模型 | {MODEL} |
| 输出文件 | Export/{STEM}.json |
| 转录段数 | {N} 段 |
| 服务状态 | 已运行 / 自动启动 |

💡 下一步：运行 `/stt.json2md Export/{STEM}.json` 将转录结果转换为 Markdown 演讲稿
```

## Behavior Rules

- **绝不跳过错误**：任何步骤失败必须立即停止并报告，不得静默继续
- **服务检测优先**：必须先确认服务可用再调用 API
- **降级而非崩溃**：服务启动失败时提供详细的手动修复步骤
- **保持幂等**：重复执行覆盖已有 JSON 文件
- **中文输出**：所有提示信息和报告使用中文
- **不修改上游**：不修改 `start.py`、stt 服务代码或任何上游文件
