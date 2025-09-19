# 文档一级标题提取助理 API

基于FastAPI的文档结构化分析API，使用AI技术提取文档的一级标题结构。

## 功能特点

- 🚀 **智能分析**: 使用AI模型自动识别文档中的一级标题
- 📄 **多格式支持**: 支持 `.txt`, `.md`, `.pdf`, `.docx`, `.doc` 等文件格式
- 🔧 **JSON输出**: 结构化的JSON格式输出，便于后续处理
- 🌐 **Web API**: 基于FastAPI的RESTful接口
- 📚 **自动文档**: 内置Swagger UI和ReDoc文档

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 启动服务

```bash
# 方法1: 使用main.py启动
python main.py

# 方法2: 直接使用uvicorn启动
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

### 2. 访问API文档

启动后访问以下地址：

- **Swagger UI**: <http://127.0.0.1:8000/docs>
- **ReDoc**: <http://127.0.0.1:8000/redoc>
- **API基础信息**: <http://127.0.0.1:8000>

## API 接口

### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 获取API基础信息 |
| `/health` | GET | 健康检查 |
| `/supported-formats` | GET | 获取支持的文件格式 |
| `/extract-sections` | POST | 提取文档一级标题结构 |

### 核心接口: `/extract-sections`

**请求方式**: POST

**请求参数**:

- `file`: 上传的文档文件（form-data格式）

**响应格式**:

```json
{
  "sections": [
    {
      "index": 1,
      "title": "第一章：概述",
      "content": "这是第一章的内容..."
    },
    {
      "index": 2,
      "title": "第二章：方法论",
      "content": "这是第二章的内容..."
    }
  ],
  "file_name": "example.txt",
  "file_size": "12.34 KB",
  "processing_status": "success"
}
```

## 使用示例

### cURL 示例

```bash
# 提取文档结构
curl -X POST "http://127.0.0.1:8000/extract-sections" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.txt"
```

### Python 客户端示例

```python
import requests

# 上传文件并提取结构
url = "http://127.0.0.1:8000/extract-sections"
files = {"file": open("your_document.txt", "rb")}

response = requests.post(url, files=files)
result = response.json()

# 打印结果
print(f"文件: {result['file_name']}")
print(f"状态: {result['processing_status']}")

for section in result['sections']:
    print(f"\n{section['index']}. {section['title']}")
    print(f"内容: {section['content'][:100]}...")
```

### JavaScript 示例

```javascript
// 使用 fetch 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://127.0.0.1:8000/extract-sections', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('处理结果:', data);
    data.sections.forEach(section => {
        console.log(`${section.index}. ${section.title}`);
    });
})
.catch(error => console.error('错误:', error));
```

## 环境变量配置

可以通过环境变量配置API的行为：

```bash
# Ollama 模型配置
export OLLAMA_MODEL="llama3.1"
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_TEMPERATURE="0.7"

# API 服务配置
export API_HOST="127.0.0.1"
export API_PORT="8000"
```

或者创建 `.env` 文件：

```env
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.7
API_HOST=127.0.0.1
API_PORT=8000
```

## 错误处理

API提供详细的错误信息：

```json
{
  "error": "不支持的文件格式: .xlsx",
  "detail": "支持的格式: .txt, .md, .pdf, .docx, .doc"
}
```

常见错误类型：

- `400 Bad Request`: 不支持的文件格式
- `422 Unprocessable Entity`: 文件无法处理
- `500 Internal Server Error`: 服务内部错误
- `503 Service Unavailable`: AI服务不可用

## 文档结构提取规则

AI会按照以下规则提取文档结构：

1. **一级标题识别**: 自动识别Markdown标题（`# 标题`）或格式化标题
2. **内容归属**: 每个标题下的内容包含到下一个一级标题之前的所有文本
3. **标题清洗**: 去除Markdown标记，保留纯文本标题
4. **空内容处理**: 无内容的标题返回空字符串
5. **表格过滤**: 自动过滤表格和图片内容
6. **无标题文档**: 返回空的sections数组

## 开发说明

### 项目结构

```
doc-agent/
├── api.py              # FastAPI应用主文件
├── main.py             # 启动脚本
├── ollama_file_chat.py # 文档处理核心模块
├── requirements.txt    # 依赖列表
├── README.md          # 使用说明
└── .env               # 环境变量配置（可选）
```

### 核心模块

- **OllamaFileChat**: 文档处理和AI交互的核心类
- **FileProcessor**: 支持多种文件格式的加载器
- **DocumentSection**: Pydantic数据模型，定义章节结构

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！
