import uvicorn


def main():
    """启动FastAPI服务"""
    print("🚀 启动文档一级标题提取助理 API 服务...")
    print("📡 服务地址: http://127.0.0.1:53518")
    print("📚 API文档: http://127.0.0.1:53518/docs")
    print("🔧 ReDoc文档: http://127.0.0.1:53518/redoc")

    uvicorn.run("api:app", host="0.0.0.0", port=53518, reload=True, log_level="info")


if __name__ == "__main__":
    main()
