"""
中医聊天机器人 - 主入口
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """打印启动横幅"""
    banner = """
    ===========================================================
    
               TCM Chatbot v1.0.0
    
       RAG + Relational Database TCM Knowledge QA System
    
    ===========================================================
    """
    print(banner)


def init_directories():
    """初始化必要的目录"""
    dirs = [
        "data/vector_db",
        "data/documents/针灸",
        "data/documents/伤寒论",
        "data/documents/金匮要略",
        "data/documents/神农本草经",
        "data/documents/医案",
        "logs",
        "plugins"
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print("[OK] Directories initialized")
    print("[INFO] 数据库使用 Supabase（需配置 SUPABASE_URL 和 SUPABASE_KEY）")


def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "chromadb",
        "langchain",
        "sentence_transformers"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️ 缺少以下依赖包: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("[OK] Dependencies check passed")
    return True


def run_api_server(host: str = "0.0.0.0", port: int = 8888, reload: bool = False):
    """运行API服务器"""
    import uvicorn
    
    print(f"\n[START] Starting API server...")
    print(f"   URL: http://{host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def run_web_ui(api_url: str = "http://localhost:8888", port: int = 7860):
    """运行Web界面"""
    try:
        from web.chat_interface import create_gradio_interface
        
        print(f"\n[START] Starting Web UI...")
        print(f"   URL: http://localhost:{port}")
        print(f"   API: {api_url}")
        
        demo = create_gradio_interface(api_url)
        if demo:
            launch_kwargs = {
                "server_name": "0.0.0.0",
                "server_port": port,
                "share": False,
                "show_error": True
            }
            # 如果有自定义CSS，传递给launch
            if hasattr(demo, 'css') and demo.css:
                launch_kwargs['css'] = demo.css
            launch_kwargs['theme'] = 'soft'
            demo.launch(**launch_kwargs)
    except ImportError as e:
        print(f"❌ 启动Web界面失败: {e}")
        print("请确保已安装Gradio: pip install gradio")


def init_database():
    """初始化数据库连接（Supabase）"""
    print("\n🗄️  初始化数据库连接...")
    
    try:
        from db import create_supabase_client
        
        client = create_supabase_client()
        
        if client:
            print("✓ Supabase 数据库连接已初始化")
            # 测试连接
            stats = client.get_collection_stats() if hasattr(client, 'get_collection_stats') else None
            if stats:
                print(f"   文档数量: {stats.get('total_documents', 'N/A')}")
        else:
            print("⚠️  Supabase 未配置")
            print("   请设置 SUPABASE_URL 和 SUPABASE_KEY 环境变量")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")


def init_vector_db():
    """初始化向量数据库"""
    print("\n📚 初始化向量数据库...")
    
    try:
        from rag.vector_store import TCMVectorStore, init_knowledge_base
        
        vector_store = TCMVectorStore(
            persist_directory="./data/vector_db",
            embedding_model="BAAI/bge-large-zh-v1.5"
        )
        
        stats = vector_store.get_collection_stats()
        print(f"[OK] Vector database initialized")
        print(f"   Documents: {stats.get('total_documents', 0)}")
        
        # 如果有文档，加载到知识库
        if stats.get('total_documents', 0) == 0:
            print("\n📖 检测到知识库为空，是否加载示例文档？(y/n)")
            # 这里可以添加交互式加载
        
    except Exception as e:
        print(f"❌ 向量数据库初始化失败: {e}")


def run_tests():
    """运行测试"""
    print("\n🧪 运行测试...")
    
    try:
        import pytest
        pytest.main(["-v", "tests/"])
    except ImportError:
        print("请安装pytest: pip install pytest")


def interactive_shell():
    """交互式命令行"""
    print("\n💬 进入交互模式")
    print("输入 'quit' 或 'exit' 退出\n")
    
    try:
        import requests
        
        api_url = "http://localhost:8888"
        session_id = None
        
        while True:
            try:
                user_input = input("您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break
                
                if not user_input:
                    continue
                
                # 发送请求
                response = requests.post(
                    f"{api_url}/chat",
                    json={"message": user_input, "session_id": session_id},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get("session_id")
                    print(f"\n助手: {data.get('message')}\n")
                else:
                    print(f"请求失败: {response.status_code}")
            
            except requests.exceptions.ConnectionError:
                print("❌ 无法连接到API服务器，请确保服务已启动")
                print(f"   尝试启动: python main.py --api\n")
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except Exception as e:
                print(f"错误: {e}")
    
    except ImportError:
        print("请安装requests: pip install requests")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="中医智能助手 - TCM Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --api              # 启动API服务器
  python main.py --web              # 启动Web界面
  python main.py --init             # 初始化数据库
  python main.py --shell            # 交互式命令行
  python main.py --all              # 启动API和Web界面
        """
    )
    
    parser.add_argument("--api", action="store_true", help="启动API服务器")
    parser.add_argument("--web", action="store_true", help="启动Web界面")
    parser.add_argument("--shell", action="store_true", help="交互式命令行")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--all", action="store_true", help="启动所有服务")
    parser.add_argument("--host", default="0.0.0.0", help="API服务器主机")
    parser.add_argument("--port", type=int, default=8888, help="API服务器端口")
    parser.add_argument("--web-port", type=int, default=7860, help="Web界面端口")
    parser.add_argument("--reload", action="store_true", help="启用热重载（开发模式）")
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 初始化目录
    init_directories()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # 初始化数据库
    if args.init:
        init_database()
        init_vector_db()
        return 0
    
    # 启动API服务器
    if args.api or args.all:
        run_api_server(args.host, args.port, args.reload)
    
    # 启动Web界面
    elif args.web:
        api_url = f"http://{args.host}:{args.port}"
        run_web_ui(api_url, args.web_port)
    
    # 交互式命令行
    elif args.shell:
        interactive_shell()
    
    # 启动所有服务
    elif args.all:
        # 在新进程中启动Web界面
        import multiprocessing
        
        api_url = f"http://{args.host}:{args.port}"
        web_process = multiprocessing.Process(
            target=run_web_ui,
            args=(api_url, args.web_port)
        )
        web_process.start()
        
        # 主进程运行API服务器
        run_api_server(args.host, args.port, args.reload)
        
        web_process.terminate()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
