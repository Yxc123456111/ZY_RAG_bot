#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 聊天界面
使用 Gradio 构建
"""

import gradio as gr
import requests
from typing import List, Dict, Tuple


def create_gradio_interface(api_url: str = "http://localhost:8888") -> gr.Blocks:
    """
    创建 Gradio 聊天界面
    
    Args:
        api_url: API 服务器地址
    
    Returns:
        Gradio Blocks 应用
    """
    
    # 检查 API 是否可用
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"[Warning] API 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"[Warning] 无法连接到 API 服务器: {e}")
        print(f"[Warning] 请确保 API 服务器已启动: python main.py --api")
    
    def chat(message: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
        """处理聊天消息"""
        if not message.strip():
            return "", history
        
        try:
            response = requests.post(
                f"{api_url}/chat",
                json={"message": message},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_message = data.get("message", "抱歉，服务暂时无法响应。")
                history.append((message, bot_message))
                return "", history
            else:
                error_msg = f"请求失败 (状态码: {response.status_code})"
                history.append((message, error_msg))
                return "", history
                
        except requests.exceptions.ConnectionError:
            error_msg = "❌ 无法连接到 API 服务器\n\n请确保服务已启动：\npython main.py --api"
            history.append((message, error_msg))
            return "", history
        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            history.append((message, error_msg))
            return "", history
    
    def knowledge_search(query: str, source_type: str) -> str:
        """知识库搜索"""
        if not query.strip():
            return "请输入搜索关键词"
        
        try:
            params = {"query": query, "k": 5}
            if source_type and source_type != "全部":
                params["source_type"] = source_type
            
            response = requests.get(
                f"{api_url}/knowledge/search",
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return "未找到相关知识"
                
                output = []
                for i, result in enumerate(results, 1):
                    content = result.get("content", "")[:200]
                    score = result.get("score", 0)
                    source = result.get("source", "")
                    output.append(f"【{i}】相似度: {score:.2f}\n来源: {source}\n内容: {content}...\n")
                
                return "\n".join(output)
            else:
                return f"搜索失败 (状态码: {response.status_code})"
                
        except Exception as e:
            return f"搜索异常: {str(e)}"
    
    def diagnose(symptoms: str) -> str:
        """中医诊断"""
        if not symptoms.strip():
            return "请输入症状描述"
        
        if len(symptoms) < 10:
            return "症状描述至少需要10个字符"
        
        try:
            response = requests.post(
                f"{api_url}/diagnosis",
                json={"symptoms": symptoms},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                output = []
                output.append(f"【证型】{data.get('syndrome_type', '未知')}")
                output.append(f"\n【病机】{data.get('pathogenesis', '未知')}")
                output.append(f"\n【治则】{data.get('treatment_principle', '未知')}")
                output.append(f"\n【分析】{data.get('analysis', '未知')}")
                
                recommendations = data.get('recommendations', [])
                if recommendations:
                    output.append("\n【建议】")
                    for rec in recommendations[:3]:
                        output.append(f"- {rec}")
                
                warnings = data.get('warnings', [])
                if warnings:
                    output.append("\n【注意】")
                    for warning in warnings:
                        output.append(f"⚠️ {warning}")
                
                return "\n".join(output)
            else:
                return f"诊断请求失败 (状态码: {response.status_code})"
                
        except Exception as e:
            return f"诊断异常: {str(e)}"
    
    # 创建界面
    with gr.Blocks(title="中医智能助手", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🏥 中医智能助手")
        gr.Markdown("基于 RAG + Supabase 的中医知识问答系统")
        
        with gr.Tab("💬 聊天"):
            chatbot = gr.Chatbot(
                height=500,
                show_copy_button=True
            )
            msg = gr.Textbox(
                label="输入您的问题",
                placeholder="例如：人参的功效是什么？",
                lines=2
            )
            with gr.Row():
                submit = gr.Button("发送", variant="primary")
                clear = gr.Button("清空")
            
            submit.click(
                fn=chat,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            msg.submit(
                fn=chat,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            clear.click(lambda: None, None, chatbot, queue=False)
        
        with gr.Tab("🔍 知识搜索"):
            with gr.Row():
                search_query = gr.Textbox(
                    label="搜索关键词",
                    placeholder="例如：桂枝汤"
                )
                source_type = gr.Dropdown(
                    label="知识来源",
                    choices=["全部", "shennong", "acupuncture", "shanghan", "jinkui", "cases"],
                    value="全部"
                )
            search_btn = gr.Button("搜索", variant="primary")
            search_output = gr.Textbox(label="搜索结果", lines=15)
            
            search_btn.click(
                fn=knowledge_search,
                inputs=[search_query, source_type],
                outputs=search_output
            )
        
        with gr.Tab("🔬 中医诊断"):
            gr.Markdown("> ⚠️ **免责声明**：本诊断仅供参考，不能替代专业医生诊断。如有不适，请及时就医。")
            symptoms_input = gr.Textbox(
                label="症状描述",
                placeholder="请详细描述您的症状，如：头痛、恶寒发热、无汗、舌苔薄白、脉浮紧等",
                lines=5
            )
            diagnose_btn = gr.Button("开始诊断", variant="primary")
            diagnose_output = gr.Textbox(label="诊断结果", lines=20)
            
            diagnose_btn.click(
                fn=diagnose,
                inputs=symptoms_input,
                outputs=diagnose_output
            )
        
        with gr.Tab("ℹ️ 关于"):
            gr.Markdown("""
            ## 功能说明
            
            ### 💬 聊天
            支持自然语言问答，可查询：
            - 神农本草经（中药性味、功效、主治）
            - 针灸穴位（定位、主治、操作）
            - 伤寒论/金匮要略（方剂组成、功效、条文）
            
            ### 🔍 知识搜索
            在向量数据库中搜索相关文档片段
            
            ### 🔬 中医诊断
            基于症状的中医辨证分析
            
            ## 技术架构
            - **关系型数据库**: Supabase
            - **向量数据库**: 本地 Chroma/Milvus
            - **API 服务**: FastAPI
            - **Web 界面**: Gradio
            """)
        
        gr.Markdown("---")
        gr.Markdown("**传承中医智慧，服务现代健康** 🏥")
    
    return demo


if __name__ == "__main__":
    # 独立运行测试
    demo = create_gradio_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)
