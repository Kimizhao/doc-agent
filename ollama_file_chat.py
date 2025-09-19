"""
Ollama 文件对话示例

这个模块演示如何使用 Ollama 分析和处理各种类型的文件，包括 PDF、Word、文本文件等。
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama

# 文档加载器
try:
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        UnstructuredWordDocumentLoader,
        UnstructuredMarkdownLoader,
    )
except ImportError:
    print("警告: 某些文档加载器可能不可用，请安装相应依赖")


def get_env(key: str, default: str = "") -> str:
    """从环境变量或 .env 文件获取配置"""
    value = os.getenv(key)
    if value:
        return value
    # 兼容 dotenv 文件
    try:
        from dotenv import load_dotenv

        load_dotenv()
        return os.getenv(key, default)
    except ImportError:
        return default


class FileProcessor:
    """文件处理器类"""

    def __init__(self):
        """初始化文件处理器"""
        self.supported_extensions = {
            ".txt": self._load_text_file,
            ".md": self._load_markdown_file,
            ".pdf": self._load_pdf_file,
            ".docx": self._load_word_file,
            ".doc": self._load_word_file,
        }
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def _load_text_file(self, file_path: str) -> str:
        """加载文本文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, "r", encoding="gbk") as file:
                return file.read()

    def _load_markdown_file(self, file_path: str) -> str:
        """加载 Markdown 文件"""
        try:
            loader = UnstructuredMarkdownLoader(file_path)
            documents = loader.load()
            return "\n".join([doc.page_content for doc in documents])
        except Exception:
            # 回退到普通文本加载
            return self._load_text_file(file_path)

    def _load_pdf_file(self, file_path: str) -> str:
        """加载 PDF 文件"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return "\n".join([doc.page_content for doc in documents])
        except Exception as e:
            raise Exception(f"无法加载 PDF 文件: {str(e)}")

    def _load_word_file(self, file_path: str) -> str:
        """加载 Word 文件"""
        try:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents = loader.load()
            return "\n".join([doc.page_content for doc in documents])
        except Exception as e:
            raise Exception(f"无法加载 Word 文件: {str(e)}")

    def is_supported_file(self, file_path: str) -> bool:
        """检查文件是否受支持"""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_extensions

    def load_file(self, file_path: str) -> str:
        """
        加载文件内容

        Args:
            file_path: 文件路径

        Returns:
            str: 文件内容

        Raises:
            Exception: 当文件不存在或不受支持时
        """
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")

        file_extension = Path(file_path).suffix.lower()
        if file_extension not in self.supported_extensions:
            raise Exception(f"不支持的文件类型: {file_extension}")

        try:
            loader_func = self.supported_extensions[file_extension]
            content = loader_func(file_path)
            return content
        except Exception as e:
            raise Exception(f"加载文件时出错: {str(e)}")

    def split_text(self, text: str) -> List[str]:
        """
        分割文本为较小的块

        Args:
            text: 要分割的文本

        Returns:
            List[str]: 分割后的文本块列表
        """
        return self.text_splitter.split_text(text)

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            Dict[str, Any]: 文件信息
        """
        if not os.path.exists(file_path):
            raise Exception(f"文件不存在: {file_path}")

        file_stats = os.stat(file_path)
        return {
            "文件名": os.path.basename(file_path),
            "文件大小": f"{file_stats.st_size / 1024:.2f} KB",
            "文件类型": Path(file_path).suffix,
            "是否支持": self.is_supported_file(file_path),
            "修改时间": file_stats.st_mtime,
        }


class OllamaFileChat:
    """基于文件的 Ollama 聊天机器人"""

    def __init__(
        self,
        model_name: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
    ):
        """
        初始化文件聊天机器人

        Args:
            model_name: 模型名称
            base_url: Ollama 服务地址
            temperature: 温度参数
        """
        self.llm = ChatOllama(
            model=model_name, base_url=base_url, temperature=temperature
        )
        self.file_processor = FileProcessor()
        self.current_file_content: Optional[str] = None
        self.current_file_path: Optional[str] = None

    def load_file(self, file_path: str) -> bool:
        """
        加载文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 加载成功返回 True，否则返回 False
        """
        try:
            self.current_file_content = self.file_processor.load_file(file_path)
            self.current_file_path = file_path
            print(f"✅ 成功加载文件: {file_path}")

            # 显示文件信息
            file_info = self.file_processor.get_file_info(file_path)
            print(f"📁 文件信息: {file_info['文件名']} ({file_info['文件大小']})")

            return True
        except Exception as e:
            print(f"❌ 加载文件失败: {str(e)}")
            return False

    def ask_about_file(self, question: str) -> str:
        """
        询问关于当前文件的问题

        Args:
            question: 用户问题

        Returns:
            str: AI 回答
        """
        if not self.current_file_content:
            return "请先加载一个文件。"

        try:
            # 构建提示词
            system_prompt = f"""你是一个文档分析专家。用户已经上传了一个文件，内容如下：

文件路径: {self.current_file_path}

文件内容:
{self.current_file_content[:3000]}...

请基于这个文件的内容回答用户的问题。如果文件内容很长，你看到的可能是截断的版本。"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=question),
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            return f"分析文件时出错: {str(e)}"

    def summarize_file(self) -> str:
        """
        总结当前文件内容

        Returns:
            str: 文件摘要
        """
        if not self.current_file_content:
            return "请先加载一个文件。"

        question = "请为这个文件提供一个详细的摘要，包括主要内容、关键点和结论。"
        return self.ask_about_file(question)

    def analyze_file_structure(self) -> str:
        """
        分析文件结构

        Returns:
            str: 结构分析
        """
        if not self.current_file_content:
            return "请先加载一个文件。"

        question = "请分析这个文件的结构和组织方式，包括章节、段落布局等。"
        return self.ask_about_file(question)

    def extract_key_points(self) -> str:
        """
        提取关键点

        Returns:
            str: 关键点列表
        """
        if not self.current_file_content:
            return "请先加载一个文件。"

        question = "请从这个文件中提取最重要的关键点，以列表形式呈现。"
        return self.ask_about_file(question)

    def extract_document_sections(self) -> str:
        """
        文档一级标题提取助理 - 将文档分解为以一级标题为单位的多个部分

        Returns:
            str: 结构化的 JSON 格式输出
        """
        if not self.current_file_content:
            return '{"sections": []}'

        try:
            # 构建专门的系统提示词
            system_prompt = """# 角色
你是一个顶级的 AI 文档结构化引擎。

# 任务
你的核心任务是分析用户提供的文档，将其分解为以一级标题为单位的多个部分，并以指定的 JSON 格式输出。

# 工作流程:
1. 解析文档格式和结构特征
2. 识别并定位所有一级标题
3. 提取每个标题下的文本内容块
4. 过滤移除表格和图片相关部分
5. 生成结构化JSON输出

# 输出格式
你必须返回一个**单一的 JSON 对象**。这个对象包含一个名为 `sections` 的键，其值是一个数组。数组中的每个对象代表一个章节，并包含以下三个字段：
- `index`: (Integer) 章节的序号，从 1 开始，依次递增。
- `title`: (String) 识别出的一级标题的纯文本。
- `content`: (String) 该一级标题下方、直到下一个一级标题出现之前的所有内容。这应包括段落、列表、引言以及所有二级、三级等子标题。

最终输出的 JSON 结构示例:
`{ "sections": [ { "index": 1, "title": "...", "content": "..." }, { "index": 2, "title": "...", "content": "..." } ] }`

# 规则与约束
1. **内容归属**: `content` 字段必须包含从当前一级标题开始（不包括标题本身），到下一个一级标题之前的所有文本。但是内容中有见附表，千万不要把附表加上放到内容中。
2. **标题清洗**: `title` 字段应为纯文本，去除任何 Markdown 标记（如 `# `）。
3. **起始内容处理**: 文档开头、在第一个一级标题出现之前的任何内容都应被忽略，不包含在任何章节的 `content` 中。
4. **空内容处理**: 如果一个一级标题下没有任何内容（紧接着就是下一个一级标题），`content` 字段应为空字符串 `""`。
5. **无标题文档**: 如果整个文档中找不到任何可识别的一级标题，你必须返回一个包含空 `sections` 数组的 JSON 对象: `{ "sections": [] }`。
6. **纯净输出**: 你的回复必须是纯粹的 JSON 格式，不包含任何解释、注释或 Markdown 的 ```json ... ``` 代码块标记。
7. 完全排除表格和图片内容。

现在，请处理以下文档："""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=self.current_file_content),
            ]

            response = self.llm.invoke(messages)
            return response.content

        except Exception as e:
            return f'{{"error": "文档结构提取时出错: {str(e)}"}}'

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式

        Returns:
            List[str]: 支持的文件扩展名列表
        """
        return list(self.file_processor.supported_extensions.keys())


def demo_file_analysis():
    """演示文件分析功能"""
    print("📁 文件分析演示")
    print("=" * 40)

    # 创建聊天机器人
    model_name = get_env("OLLAMA_MODEL", "llama3.1")
    base_url = get_env("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature = float(get_env("OLLAMA_TEMPERATURE", "0.7"))
    file_chat = OllamaFileChat(
        model_name=model_name, base_url=base_url, temperature=temperature
    )

    # 显示支持的格式
    print("支持的文件格式:", file_chat.get_supported_formats())

    # 创建一个示例文件进行测试
    test_file_path = "test_document.txt"
    test_content = """
人工智能技术发展报告

第一章：概述
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。

第二章：发展历程
1. 1950年代：AI概念诞生
2. 1960-1970年代：早期专家系统
3. 1980年代：机器学习兴起
4. 2010年代：深度学习革命

第三章：主要技术
- 机器学习
- 深度学习
- 自然语言处理
- 计算机视觉
- 机器人技术

第四章：应用领域
AI技术已经广泛应用于医疗、金融、教育、交通等多个领域，极大地提高了效率和准确性。

结论：
人工智能技术正在快速发展，将继续改变我们的生活和工作方式。
    """

    # 创建测试文件
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    try:
        # 加载文件
        if file_chat.load_file(test_file_path):
            print("\n📊 生成文件摘要...")
            summary = file_chat.summarize_file()
            print(f"摘要: {summary}\n")

            print("🔍 分析文件结构...")
            structure = file_chat.analyze_file_structure()
            print(f"结构: {structure}\n")

            print("🎯 提取关键点...")
            key_points = file_chat.extract_key_points()
            print(f"关键点: {key_points}\n")

            print("📋 提取文档结构...")
            sections = file_chat.extract_document_sections()
            print(f"文档结构: {sections}\n")

            print("❓ 回答自定义问题...")
            custom_answer = file_chat.ask_about_file("这个文档提到了哪些AI技术？")
            print(f"回答: {custom_answer}")

    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


def interactive_file_chat():
    """交互式文件聊天"""
    print("🤖 Ollama 文件对话系统")
    print("=" * 40)

    model_name = get_env("OLLAMA_MODEL", "llama3.1")
    base_url = get_env("OLLAMA_BASE_URL", "http://localhost:11434")
    temperature = float(get_env("OLLAMA_TEMPERATURE", "0.7"))
    file_chat = OllamaFileChat(
        model_name=model_name, base_url=base_url, temperature=temperature
    )
    print(f"支持的文件格式: {', '.join(file_chat.get_supported_formats())}")

    while True:
        try:
            print("\n可用命令:")
            print("1. load <文件路径> - 加载文件")
            print("2. ask <问题> - 询问关于文件的问题")
            print("3. summary - 生成文件摘要")
            print("4. structure - 分析文件结构")
            print("5. keypoints - 提取关键点")
            print("6. sections - 提取文档一级标题结构")
            print("7. exit - 退出")

            user_input = input("\n请输入命令: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("再见！")
                break

            elif user_input.startswith("load "):
                file_path = user_input[5:].strip()
                file_chat.load_file(file_path)

            elif user_input.startswith("ask "):
                question = user_input[4:].strip()
                if question:
                    print("🤔 AI 正在分析...")
                    answer = file_chat.ask_about_file(question)
                    print(f"💡 回答: {answer}")
                else:
                    print("请提供问题内容")

            elif user_input.lower() == "summary":
                print("📝 生成摘要...")
                summary = file_chat.summarize_file()
                print(f"📋 摘要: {summary}")

            elif user_input.lower() == "structure":
                print("🔍 分析结构...")
                structure = file_chat.analyze_file_structure()
                print(f"🏗️ 结构: {structure}")

            elif user_input.lower() == "keypoints":
                print("🎯 提取关键点...")
                key_points = file_chat.extract_key_points()
                print(f"✨ 关键点: {key_points}")

            elif user_input.lower() == "sections":
                print("📋 提取文档一级标题结构...")
                sections = file_chat.extract_document_sections()
                print(f"📑 文档结构: {sections}")

            else:
                print("未知命令，请重试")

        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")


def main():
    """主函数"""
    print("🚀 Ollama 文件对话示例")
    print("=" * 50)

    print("\n请选择运行模式:")
    print("1. 文件分析演示")
    print("2. 交互式文件聊天")

    try:
        choice = input("\n请输入选择 (1-2): ").strip()

        if choice == "1":
            demo_file_analysis()
        elif choice == "2":
            interactive_file_chat()
        else:
            print("无效选择，默认启动交互式文件聊天")
            interactive_file_chat()

    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"发生错误: {str(e)}")


if __name__ == "__main__":
    main()
