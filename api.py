"""
文档一级标题提取助理 API

基于FastAPI实现的文档结构化分析API，支持多种文件格式的一级标题提取。
"""

import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ollama_file_chat import OllamaFileChat, get_env


# Pydantic 数据模型
class DocumentSection(BaseModel):
    """文档章节模型"""

    index: int = Field(..., description="章节序号，从1开始")
    title: str = Field(..., description="一级标题的纯文本")
    content: str = Field(..., description="该标题下的所有内容")


class DocumentSectionsResponse(BaseModel):
    """文档结构提取响应模型"""

    sections: List[DocumentSection] = Field(..., description="文档章节列表")
    file_name: Optional[str] = Field(None, description="文件名")
    file_size: Optional[str] = Field(None, description="文件大小")
    processing_status: str = Field(..., description="处理状态")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误描述")


# 创建FastAPI应用
app = FastAPI(
    title="文档一级标题提取助理",
    description="使用AI分析文档，提取一级标题结构的API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
file_chat: Optional[OllamaFileChat] = None


def initialize_file_chat():
    """初始化文件聊天机器人"""
    global file_chat
    if file_chat is None:
        model_name = get_env("OLLAMA_MODEL", "llama3.1")
        base_url = get_env("OLLAMA_BASE_URL", "http://localhost:11434")
        temperature = float(get_env("OLLAMA_TEMPERATURE", "0.7"))

        try:
            file_chat = OllamaFileChat(
                model_name=model_name, base_url=base_url, temperature=temperature
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"初始化AI模型失败: {str(e)}",
            )


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    initialize_file_chat()


@app.get("/", response_model=dict)
async def root():
    """根路径，返回API信息"""
    return {
        "message": "文档一级标题提取助理 API",
        "version": "1.0.0",
        "description": "支持多种文件格式的文档结构化分析",
        "endpoints": {
            "extract_sections": "/api/python/doc-agent/extract-sections",
            "health": "/api/python/doc-agent/health",
            "supported_formats": "/api/python/doc-agent/supported-formats",
        },
    }


@app.get("/api/python/doc-agent/health", response_model=dict)
async def health_check():
    """健康检查端点"""
    try:
        initialize_file_chat()
        return {
            "status": "healthy",
            "ai_model": get_env("OLLAMA_MODEL", "llama3.1"),
            "base_url": get_env("OLLAMA_BASE_URL", "http://localhost:11434"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"服务不可用: {str(e)}",
        )


@app.get("/api/python/doc-agent/supported-formats", response_model=dict)
async def get_supported_formats():
    """获取支持的文件格式"""
    initialize_file_chat()
    return {
        "supported_formats": file_chat.get_supported_formats(),
        "description": "支持的文件扩展名列表",
    }


@app.post(
    "/api/python/doc-agent/extract-sections", response_model=DocumentSectionsResponse
)
async def extract_document_sections(
    file: UploadFile = File(..., description="要分析的文档文件")
):
    """
    提取文档的一级标题结构

    支持的文件格式：.txt, .md, .pdf, .docx, .doc

    返回JSON格式的文档结构，包含每个章节的标题和内容
    """
    initialize_file_chat()

    # 检查文件类型
    file_extension = Path(file.filename or "").suffix.lower()
    supported_formats = file_chat.get_supported_formats()

    if file_extension not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式: {file_extension}。支持的格式: {', '.join(supported_formats)}",
        )

    # 创建临时文件
    temp_file_path = None
    try:
        # 读取上传的文件内容
        content = await file.read()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        # 加载文件到聊天机器人
        if not file_chat.load_file(temp_file_path):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="无法加载文件内容",
            )

        # 获取文件信息
        file_info = file_chat.file_processor.get_file_info(temp_file_path)

        # 提取文档结构
        sections_json = file_chat.extract_document_sections()

        try:
            # 解析JSON结果
            sections_data = json.loads(sections_json)

            # 检查是否有错误
            if "error" in sections_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=sections_data["error"],
                )

            # 构建响应
            sections = []
            for section_data in sections_data.get("sections", []):
                sections.append(
                    DocumentSection(
                        index=section_data["index"],
                        title=section_data["title"],
                        content=section_data["content"],
                    )
                )

            return DocumentSectionsResponse(
                sections=sections,
                file_name=file.filename,
                file_size=file_info.get("文件大小", "未知"),
                processing_status="success",
            )

        except json.JSONDecodeError as e:
            # 如果JSON解析失败，返回原始响应作为错误信息
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI响应格式错误: {str(e)}。原始响应: {sections_json[:200]}...",
            )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 捕获其他异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理文件时发生错误: {str(e)}",
        )

    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "内部服务器错误", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    # 从环境变量获取配置
    host = get_env("API_HOST", "127.0.0.1")
    port = int(get_env("API_PORT", "8000"))

    print(f"🚀 启动文档一级标题提取助理 API")
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"🔧 ReDoc文档: http://{host}:{port}/redoc")

    uvicorn.run("api:app", host=host, port=port, reload=True, log_level="info")
