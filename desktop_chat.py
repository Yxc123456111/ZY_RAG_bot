#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中医智能助手 - 桌面聊天客户端
使用 ttkbootstrap 创建现代化聊天界面
连接实际项目API
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Callable
import json
import requests
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入配置管理器
from config_manager import get_config, is_supabase_ready, get_supabase_url, get_supabase_key

# 导入Supabase数据库客户端
from db import SupabaseClient

# 导入意图分类器
from core.intent_classifier import QueryRouter

# 初始化配置
config = get_config()
print(f"[INFO] 配置管理器已初始化")
print(f"[INFO] Supabase 配置状态: {'已配置' if is_supabase_ready() else '未配置'}")


class ChatMessage:
    """聊天消息类"""
    def __init__(self, content: str, is_user: bool = True, timestamp: Optional[str] = None):
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")


class Conversation:
    """会话类"""
    def __init__(self, id: str, title: str, messages: List[ChatMessage] = None):
        self.id = id
        self.title = title
        self.messages = messages or []
        self.last_time = datetime.now().strftime("%m-%d %H:%M")
        self.session_id = None


class TCMAPIClient:
    """TCM API 客户端 - 连接实际项目API和Supabase"""
    
    def __init__(self, api_url: str = "http://localhost:8888"):
        self.api_url = api_url
        self.timeout = 30
        # 初始化Supabase客户端
        self.supabase_client = self._init_supabase_client()
        
    def _init_supabase_client(self) -> Optional[SupabaseClient]:
        """初始化Supabase客户端"""
        try:
            from db import create_supabase_client
            client = create_supabase_client()
            if client:
                print("[INFO] Supabase客户端初始化成功")
            return client
        except Exception as e:
            print(f"[Warning] Supabase客户端初始化失败: {e}")
            return None
        
    def query_supabase_herb(self, drug_name: str) -> Dict:
        """
        从Supabase查询草药信息
        
        Returns:
            {
                "success": bool,
                "drug_name": str,
                "data": Dict,
                "message": str,
                "error": str (optional)
            }
        """
        if not self.supabase_client:
            return {
                "success": False,
                "drug_name": drug_name,
                "message": "Supabase客户端未配置，请检查SUPABASE_URL和SUPABASE_KEY",
                "error": "CLIENT_NOT_INITIALIZED"
            }
        
        try:
            # 使用新的Supabase客户端查询
            result = self.supabase_client.query_shennong_herb(drug_name)
            
            if result:
                # 格式化结果
                formatted = self.supabase_client.format_shennong_herb(result)
                return {
                    "success": True,
                    "drug_name": result.get("drug_name", drug_name),
                    "data": result,
                    "formatted": formatted,
                    "message": f"找到草药：{result.get('drug_name', drug_name)}"
                }
            else:
                # 尝试模糊搜索
                suggestions = self.supabase_client.search_shennong_herbs(drug_name, limit=5)
                if suggestions:
                    suggestion_names = [item.get("drug_name", "") for item in suggestions]
                    return {
                        "success": False,
                        "drug_name": drug_name,
                        "message": f"未找到'{drug_name}'",
                        "suggestions": suggestion_names,
                        "error": "NOT_FOUND"
                    }
                
                return {
                    "success": False,
                    "drug_name": drug_name,
                    "message": f"数据库中未找到'{drug_name}'",
                    "error": "NOT_FOUND"
                }
                
        except Exception as e:
            return {
                "success": False,
                "drug_name": drug_name,
                "message": f"查询出错：{str(e)}",
                "error": "EXCEPTION"
            }
    
    def _clean_herb_text(self, text: str) -> str:
        """清理文本，移除以 > 开头的额外解释段落"""
        if not text:
            return ""
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # 跳过以 > 开头的行（额外解释）
            if stripped.startswith('>'):
                continue
            # 跳过空行
            if stripped:
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    def _format_herb_info(self, herb: Dict) -> str:
        """格式化草药信息为可读文本"""
        lines = []
        lines.append(f"【{herb.get('drug_name', '未知药物')}】")
        lines.append("")
        
        if herb.get('original_text'):
            lines.append("[本经原文]")
            lines.append(self._clean_herb_text(herb['original_text']))
            lines.append("")
        
        if herb.get('properties'):
            lines.append("[性味]")
            lines.append(self._clean_herb_text(herb['properties']))
            lines.append("")
        
        if herb.get('origin'):
            lines.append("[产地]")
            lines.append(self._clean_herb_text(herb['origin']))
            lines.append("")
        
        if herb.get('indications'):
            lines.append("[主治]")
            lines.append(self._clean_herb_text(herb['indications']))
            lines.append("")
        
        if herb.get('dosage'):
            lines.append("[用量]")
            lines.append(self._clean_herb_text(herb['dosage']))
            lines.append("")
        
        if herb.get('contraindications'):
            lines.append("[禁忌]")
            lines.append(self._clean_herb_text(herb['contraindications']))
            lines.append("")
        
        # 添加其他字段（历代医家论述）
        for i in range(1, 12):
            other_name = herb.get(f"other{i}_name")
            other_content = herb.get(f"other{i}")
            if other_name and other_content:
                cleaned_content = self._clean_herb_text(other_content)
                if cleaned_content:
                    lines.append(f"[{other_name}]")
                    lines.append(cleaned_content)
                    lines.append("")
        
        # 添加查询出处
        lines.append("─" * 40)
        lines.append("📚 查询出处：神农本草经")
        lines.append("数据来源：Supabase 数据库")
        
        return "\n".join(lines)
        
    def check_health(self) -> Dict:
        """检查API服务状态"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": f"HTTP {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "offline", "message": "无法连接到服务器"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict:
        """
        发送聊天消息
        
        Returns:
            {
                "success": bool,
                "message": str,
                "session_id": str,
                "intent": str,
                "data_type": str,
                "sources": List[Dict],
                "confidence": float,
                "error": str (optional)
            }
        """
        try:
            response = requests.post(
                f"{self.api_url}/chat",
                json={
                    "message": message,
                    "session_id": session_id
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": data.get("message", "抱歉，没有获取到回复"),
                    "session_id": data.get("session_id"),
                    "intent": data.get("intent", "unknown"),
                    "data_type": data.get("data_type", "direct"),
                    "sources": data.get("sources", []),
                    "confidence": data.get("confidence", 0.0)
                }
            else:
                return {
                    "success": False,
                    "error": f"请求失败：HTTP {response.status_code}",
                    "message": f"服务器返回错误：{response.status_code}"
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "connection_error",
                "message": "无法连接到服务器，请确保API服务已启动 (python main.py --api)"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "timeout",
                "message": "请求超时，请稍后重试"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"发生错误：{str(e)}"
            }
    
    def diagnose(self, symptoms: str, include_sources: List[str] = None) -> Dict:
        """
        进行病情诊断
        
        Returns:
            {
                "success": bool,
                "syndrome_type": str,
                "pathogenesis": str,
                "treatment_principle": str,
                "recommendations": List[Dict],
                "analysis": str,
                "sources": List[Dict],
                "confidence": float,
                "warnings": List[str],
                "error": str (optional)
            }
        """
        try:
            payload = {"symptoms": symptoms}
            if include_sources:
                payload["include_sources"] = include_sources
                
            response = requests.post(
                f"{self.api_url}/diagnosis",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "syndrome_type": data.get("syndrome_type", "未知"),
                    "pathogenesis": data.get("pathogenesis", ""),
                    "treatment_principle": data.get("treatment_principle", ""),
                    "recommendations": data.get("recommendations", []),
                    "analysis": data.get("analysis", ""),
                    "sources": data.get("sources", []),
                    "confidence": data.get("confidence", 0.0),
                    "warnings": data.get("warnings", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"请求失败：HTTP {response.status_code}",
                    "message": f"诊断请求失败：{response.status_code}"
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "connection_error",
                "message": "无法连接到服务器，请确保API服务已启动"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"诊断发生错误：{str(e)}"
            }
    
    def search_knowledge(self, query: str, source_type: Optional[str] = None, k: int = 5) -> Dict:
        """
        搜索知识库
        
        Returns:
            {
                "success": bool,
                "query": str,
                "count": int,
                "results": List[Dict],
                "error": str (optional)
            }
        """
        try:
            params = {"query": query, "k": k}
            if source_type and source_type != "全部":
                params["source_type"] = source_type
            
            response = requests.get(
                f"{self.api_url}/knowledge/search",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "query": data.get("query", query),
                    "count": data.get("count", 0),
                    "results": data.get("results", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"请求失败：HTTP {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_schema(self, table: Optional[str] = None) -> Dict:
        """获取数据库结构"""
        try:
            url = f"{self.api_url}/schema"
            if table:
                url = f"{url}/{table}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TCMChatApp:
    """中医智能助手桌面应用"""
    
    def __init__(self, root: ttkb.Window):
        self.root = root
        self.root.title("中医聊天机器人")
        self.root.geometry("1800x1200")
        self.root.minsize(1200, 800)
        
        # 设置主题 - 深色主题
        self.style = ttkb.Style(theme="darkly")
        
        # 定义深色主题配色
        self.COLORS = {
            'bg_dark': '#0f172a',        # 深蓝黑背景
            'bg_sidebar': '#1e293b',     # 侧边栏背景
            'bg_card': '#1e293b',        # 卡片背景
            'bg_input': '#334155',       # 输入框背景
            'text_primary': '#f8fafc',   # 主文字白色
            'text_secondary': '#94a3b8', # 次文字灰色
            'accent': '#3b82f6',         # 强调色蓝色
            'accent_hover': '#2563eb',   # 强调色悬停
            'border': '#334155',         # 边框色
        }
        
        # 数据
        self.conversations: List[Conversation] = []
        self.current_conversation: Optional[Conversation] = None
        self.message_frames: List[ttkb.Frame] = []
        
        # 草药查询模式
        self.herb_query_mode = False  # 是否处于草药查询模式
        self.herb_query_title = "[草药查询模式]"
        
        # API客户端 - 端口8888（与API服务一致）
        API_PORT = 8888
        print(f"[INFO] Connecting to API on port {API_PORT}")
        self.api_client = TCMAPIClient(api_url=f"http://localhost:{API_PORT}")
        
        # 初始化UI
        self._init_ui()
        self._check_api_status()
        self._create_welcome_conversation()
        
    def _init_ui(self):
        """初始化用户界面"""
        # 主容器
        self.main_container = tk.Frame(self.root, bg=self.COLORS['bg_dark'])
        self.main_container.pack(fill=BOTH, expand=True)
        
        # 左侧边栏 - 会话列表
        self._create_sidebar()
        
        # 右侧主区域 - 聊天界面
        self._create_chat_area()
        
    def _create_rounded_button(self, parent, text, command, bg, fg, hover_bg, 
                               font=("Microsoft YaHei", 10), height=36, radius=8):
        """创建圆角按钮"""
        btn_frame = tk.Frame(parent, bg=parent.cget("bg"))
        
        # 创建Canvas
        canvas = tk.Canvas(btn_frame, height=height, bg=parent.cget("bg"), 
                          highlightthickness=0)
        canvas.pack(fill=X)
        
        # 等待框架布局完成
        def draw_button(event=None):
            width = btn_frame.winfo_width() or 200
            
            # 绘制圆角矩形
            def round_rect(x1, y1, x2, y2, r, **kwargs):
                points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                         x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
                return canvas.create_polygon(points, smooth=True, **kwargs)
            
            canvas.delete("all")
            round_rect(2, 2, width-2, height-2, radius, fill=bg, outline="")
            
            # 添加文字
            canvas.create_text(width//2, height//2, text=text, font=font, fill=fg)
        
        # 绑定尺寸变化事件
        btn_frame.bind("<Configure>", draw_button)
        
        # 初始绘制
        btn_frame.after(10, draw_button)
        
        # 绑定点击事件
        def on_click(event):
            if command:
                command()
        
        def on_enter(event):
            width = btn_frame.winfo_width() or 200
            canvas.delete("all")
            
            def round_rect(x1, y1, x2, y2, r, **kwargs):
                points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                         x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
                return canvas.create_polygon(points, smooth=True, **kwargs)
            
            round_rect(2, 2, width-2, height-2, radius, fill=hover_bg, outline="")
            canvas.create_text(width//2, height//2, text=text, font=font, fill=fg)
            canvas.config(cursor="hand2")
        
        def on_leave(event):
            width = btn_frame.winfo_width() or 200
            canvas.delete("all")
            
            def round_rect(x1, y1, x2, y2, r, **kwargs):
                points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
                         x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
                return canvas.create_polygon(points, smooth=True, **kwargs)
            
            round_rect(2, 2, width-2, height-2, radius, fill=bg, outline="")
            canvas.create_text(width//2, height//2, text=text, font=font, fill=fg)
        
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        return btn_frame
    
    def _create_sidebar(self):
        """创建左侧边栏 - 深色布局"""
        # 侧边栏容器
        self.sidebar = tk.Frame(self.main_container, width=280, bg=self.COLORS['bg_sidebar'])
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)
        
        # 顶部 - 新建对话按钮（圆角设计）
        header = tk.Frame(self.sidebar, bg=self.COLORS['bg_sidebar'])
        header.pack(fill=X, padx=16, pady=16)
        
        # 新建对话按钮 - 使用Canvas绘制圆角
        self._create_rounded_button(
            header, "+ 新建对话", self._new_conversation,
            bg=self.COLORS['bg_card'], fg=self.COLORS['text_primary'],
            hover_bg="#334155", font=("Microsoft YaHei", 11, "bold"),
            height=44
        ).pack(fill=X)
        
        # 快捷查询区域 - 深色风格
        quick_frame = tk.Frame(self.sidebar, bg=self.COLORS['bg_sidebar'])
        quick_frame.pack(fill=X, padx=16, pady=(0, 16))
        
        # 快捷查询标题 - 蓝色高亮
        quick_title = tk.Label(quick_frame, text="试试询问：", font=("Microsoft YaHei", 10, "bold"), 
                               bg=self.COLORS['bg_sidebar'], fg=self.COLORS['accent'])
        quick_title.pack(anchor="w", pady=(0, 8))
        
        # 快捷功能按钮容器
        quick_btn_container = tk.Frame(quick_frame, bg=self.COLORS['bg_sidebar'])
        quick_btn_container.pack(fill=X)
        
        # 快捷功能按钮 - 圆角设计
        quick_buttons = [
            ("▸ 穴位查询", self._quick_acupuncture),
            ("▸ 中药查询", self._quick_herb),
            ("▸ 方剂查询", self._quick_formula),
            ("▸ 症状诊断", self._quick_diagnosis),
        ]
        
        for text, command in quick_buttons:
            self._create_rounded_button(
                quick_btn_container, text, command,
                bg=self.COLORS['bg_sidebar'], fg=self.COLORS['text_secondary'],
                hover_bg="#334155", font=("Microsoft YaHei", 10),
                height=36, radius=6
            ).pack(fill=X, pady=3)
        
        # 会话列表容器（隐藏，保留功能但不在UI显示）
        self.conversation_list = ScrolledFrame(self.sidebar, autohide=True)
        # 不pack，隐藏对话列表
        
        # 弹性空间 - 将底部按钮推到底部
        spacer = tk.Frame(self.sidebar, bg=self.COLORS['bg_sidebar'])
        spacer.pack(fill=BOTH, expand=True)
        
        # 底部 - 其他功能按钮
        bottom_frame = tk.Frame(self.sidebar, bg=self.COLORS['bg_sidebar'])
        bottom_frame.pack(fill=X, padx=16, pady=8, side=BOTTOM)
        
        # 功能按钮 - 圆角设计
        func_buttons = [
            ("知识库", self._show_knowledge),
            ("设置", self._show_settings),
        ]
        
        for text, command in func_buttons:
            self._create_rounded_button(
                bottom_frame, text, command,
                bg=self.COLORS['bg_sidebar'], fg=self.COLORS['text_secondary'],
                hover_bg="#334155", font=("Microsoft YaHei", 10),
                height=36, radius=6
            ).pack(fill=X, pady=3)
        
        # API状态指示器 - 深色样式
        self.api_status_frame = tk.Frame(bottom_frame, bg=self.COLORS['bg_sidebar'])
        self.api_status_frame.pack(fill=X, pady=(12, 0))
        
        # 状态指示点
        self.status_dot = tk.Label(self.api_status_frame, text="●", font=("Microsoft YaHei", 9), 
                                   bg=self.COLORS['bg_sidebar'], fg="#F59E0B")
        self.status_dot.pack(side=LEFT)
        
        self.api_status_label = tk.Label(
            self.api_status_frame,
            text="检查中...",
            font=("Microsoft YaHei", 9),
            bg=self.COLORS['bg_sidebar'],
            fg=self.COLORS['text_secondary']
        )
        self.api_status_label.pack(side=LEFT, padx=(4, 0))
            
    def _create_chat_area(self):
        """创建聊天主区域 - 深色布局"""
        # 聊天区域容器
        self.chat_container = tk.Frame(self.main_container, bg=self.COLORS['bg_dark'])
        self.chat_container.pack(side=LEFT, fill=BOTH, expand=True)
        
        # 消息显示区域
        self.message_area = ScrolledFrame(self.chat_container, autohide=True)
        self.message_area.pack(fill=BOTH, expand=True, padx=24, pady=24)
        
        # 输入区域
        self._create_input_area()
        
    def _create_input_area(self):
        """创建输入区域 - 深色圆角设计"""
        # 输入区域容器
        input_outer = tk.Frame(self.chat_container, bg=self.COLORS['bg_dark'])
        input_outer.pack(fill=X, padx=24, pady=(0, 24))
        
        input_container = tk.Frame(input_outer, bg=self.COLORS['bg_dark'])
        input_container.pack(fill=X)
        
        # 输入框框架 - 深色圆角背景
        input_frame = tk.Frame(input_container, bg=self.COLORS['bg_input'], padx=4, pady=4)
        input_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 12))
        
        # 输入框 - 深色背景
        self.input_text = tk.Text(
            input_frame,
            height=2,
            font=("Microsoft YaHei", 12),
            bg=self.COLORS['bg_input'],
            fg=self.COLORS['text_secondary'],
            insertbackground=self.COLORS['accent'],
            relief=FLAT,
            wrap=WORD,
            padx=16,
            pady=12,
            highlightthickness=0
        )
        self.input_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.input_text.bind("<Return>", self._on_enter_pressed)
        self.input_text.bind("<Shift-Return>", self._on_shift_enter)
        
        # 占位符提示
        self.input_text.insert("1.0", "输入您的问题...")
        
        def on_focus_in(event):
            if self.input_text.get("1.0", END).strip() == "输入您的问题...":
                self.input_text.delete("1.0", END)
                self.input_text.config(fg=self.COLORS['text_primary'])
        
        def on_focus_out(event):
            # 失去焦点时如果为空，显示占位符
            if self.input_text.get("1.0", END).strip() == "":
                self.input_text.insert("1.0", "输入您的问题...")
                self.input_text.config(fg=self.COLORS['text_secondary'])
        
        self.input_text.bind("<FocusIn>", on_focus_in)
        self.input_text.bind("<FocusOut>", on_focus_out)
        
        # 发送按钮 - 蓝色圆形（使用Canvas绘制）
        send_canvas = tk.Canvas(input_container, width=48, height=48, 
                               bg=self.COLORS['bg_dark'], highlightthickness=0)
        send_canvas.pack(side=RIGHT)
        
        # 绘制蓝色圆形
        send_canvas.create_oval(4, 4, 44, 44, fill=self.COLORS['accent'], 
                               outline=self.COLORS['accent'])
        # 绘制纸飞机图标（简化为三角形）
        send_canvas.create_polygon(18, 16, 32, 24, 18, 32, fill="white", outline="white")
        
        # 绑定点击事件
        send_canvas.bind("<Button-1>", lambda e: self._send_message())
        
    def _check_api_status(self):
        """检查Supabase连接状态"""
        def check():
            try:
                # 使用Supabase客户端测试连接
                if self.api_client.supabase_client:
                    # 尝试查询一个药物来测试连接
                    result = self.api_client.supabase_client.query_shennong_herb("人参")
                    if result is not None:
                        result = {"status": "connected", "message": "Supabase已连接"}
                    else:
                        # 查询返回None也可能是连接正常但药物不存在，再尝试搜索
                        search_result = self.api_client.supabase_client.search_shennong_herbs("人", limit=1)
                        if search_result is not None:
                            result = {"status": "connected", "message": "Supabase已连接"}
                        else:
                            result = {"status": "offline", "message": "无法查询数据库"}
                else:
                    result = {"status": "offline", "message": "Supabase客户端未初始化"}
            except Exception as e:
                result = {"status": "offline", "message": str(e)}
            
            self.root.after(0, self._update_api_status, result)
        
        threading.Thread(target=check, daemon=True).start()
    
    def _update_api_status(self, result: Dict):
        """更新Supabase连接状态显示"""
        status = result.get("status", "unknown")
        
        if status == "connected":
            self.status_dot.config(fg="#10B981")  # 绿色
            self.api_status_label.config(text="已连接", fg="#10B981")
        elif status == "offline":
            self.status_dot.config(fg="#EF4444")  # 红色
            self.api_status_label.config(text="离线", fg="#EF4444")
        else:
            self.status_dot.config(fg="#F59E0B")  # 黄色
            self.api_status_label.config(text="连接中...", fg="#F59E0B")
        
    def _create_welcome_conversation(self):
        """创建欢迎会话 - 深色气泡风格"""
        welcome_conv = Conversation("welcome", "新建对话", [])
        
        # 深色气泡风格的欢迎消息
        welcome_msg = ChatMessage(
            "欢迎使用中医智能助手！我可以帮您查询穴位、中药、方剂，以及进行症状诊断。请输入您的问题。",
            is_user=False
        )
        welcome_conv.messages.append(welcome_msg)
        
        self.conversations.append(welcome_conv)
        self._refresh_conversation_list()
        self._select_conversation(welcome_conv)
        
    def _refresh_conversation_list(self):
        """刷新会话列表"""
        # 清除现有内容
        for widget in self.conversation_list.winfo_children():
            widget.destroy()
            
        # 添加会话项
        for conv in self.conversations:
            self._create_conversation_item(conv)
            
    def _create_conversation_item(self, conv: Conversation):
        """创建会话列表项 - 简洁设计，支持右键删除"""
        item_frame = tk.Frame(self.conversation_list, bg="white")
        item_frame.pack(fill=X, pady=2, padx=5)
        
        # 选中状态
        is_selected = self.current_conversation and self.current_conversation.id == conv.id
        
        # 背景色
        bg_color = "#F1F5F9" if is_selected else "white"
        fg_color = "#1E293B" if is_selected else "#475569"
        
        # 主按钮框架
        btn_frame = tk.Frame(item_frame, bg=bg_color, padx=12, pady=10)
        btn_frame.pack(fill=X)
        btn_frame.bind("<Button-1>", lambda e, c=conv: self._select_conversation(c))
        
        # 标题标签
        title_label = tk.Label(
            btn_frame,
            text=conv.title,
            font=("Microsoft YaHei", 10),
            bg=bg_color,
            fg=fg_color,
            anchor="w"
        )
        title_label.pack(fill=X)
        title_label.bind("<Button-1>", lambda e, c=conv: self._select_conversation(c))
        
        # 时间标签 - 显示在标题下方
        time_label = tk.Label(
            btn_frame,
            text=conv.last_time,
            font=("Microsoft YaHei", 8),
            bg=bg_color,
            fg="#94A3B8",
            anchor="w"
        )
        time_label.pack(fill=X, pady=(2, 0))
        time_label.bind("<Button-1>", lambda e, c=conv: self._select_conversation(c))
        
        # 绑定右键菜单到整个框架
        for widget in [item_frame, btn_frame, title_label, time_label]:
            widget.bind("<Button-3>", lambda e, c=conv: self._show_conversation_context_menu(e, c))
    
    def _show_conversation_context_menu(self, event, conv: Conversation):
        """显示会话右键菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="删除对话", command=lambda: self._delete_conversation_by_obj(conv))
        
        try:
            menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def _delete_conversation_by_obj(self, conv: Conversation):
        """根据会话对象删除对话"""
        if conv not in self.conversations:
            return
            
        if messagebox.askyesno("确认", f"确定要删除对话\"{conv.title}\"吗？"):
            self.conversations.remove(conv)
            
            # 如果删除的是当前选中的对话，新建一个对话
            if self.current_conversation == conv:
                self.current_conversation = None
                if self.conversations:
                    self._select_conversation(self.conversations[0])
                else:
                    self._new_conversation()
            else:
                self._refresh_conversation_list()
        
    def _select_conversation(self, conv: Conversation):
        """选择会话"""
        self.current_conversation = conv
        
        # 根据会话标题判断是否进入草药查询模式
        if conv.title == self.herb_query_title:
            self.herb_query_mode = True
        else:
            self.herb_query_mode = False
        
        self._refresh_conversation_list()
        self._display_messages(conv.messages)
        
    def _display_messages(self, messages: List[ChatMessage]):
        """显示消息列表"""
        # 清除现有消息
        for widget in self.message_area.winfo_children():
            widget.destroy()
        self.message_frames.clear()
        
        # 显示每条消息
        for msg in messages:
            self._add_message_to_display(msg)
    
    def _add_system_message(self, content: str):
        """添加系统消息（居中显示，用于提示信息）"""
        # 消息外层容器
        msg_container = tk.Frame(self.message_area, bg=self.COLORS['bg_dark'])
        msg_container.pack(fill=X, pady=16)
        msg_container.pack_configure(anchor="center")
        
        # 系统消息气泡 - 绿色背景（草药主题）
        content_frame = tk.Frame(msg_container, bg=self.COLORS['bg_dark'])
        content_frame.pack()
        
        bubble = tk.Frame(content_frame, bg="#059669", padx=2, pady=2)
        bubble.pack()
        
        # 消息文本
        content_label = tk.Label(
            bubble,
            text=content,
            wraplength=700,
            justify=LEFT,
            font=("Microsoft YaHei", 11),
            bg="#059669",
            fg="white"
        )
        content_label.pack(padx=24, pady=16)
        
        self.message_frames.append(msg_container)
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """滚动消息区域到底部"""
        self.message_area.update_idletasks()
        self.message_canvas.yview_moveto(1.0)
            
    def _add_message_to_display(self, msg: ChatMessage):
        """添加单条消息到显示区域 - 深色气泡设计"""
        # 消息外层容器
        msg_container = tk.Frame(self.message_area, bg=self.COLORS['bg_dark'])
        msg_container.pack(fill=X, pady=16)
        
        if msg.is_user:
            # 用户消息 - 右侧对齐
            msg_container.pack_configure(anchor="e")
            
            # 消息内容框架
            content_frame = tk.Frame(msg_container, bg=self.COLORS['bg_dark'])
            content_frame.pack(side=RIGHT)
            
            # 用户消息气泡 - 蓝色背景（类似发送按钮）
            bubble = tk.Frame(content_frame, bg=self.COLORS['accent'], padx=2, pady=2)
            bubble.pack(side=RIGHT, padx=(100, 0))
            
            # 消息文本
            content = tk.Label(
                bubble,
                text=msg.content,
                wraplength=700,
                justify=LEFT,
                font=("Microsoft YaHei", 11),
                bg=self.COLORS['accent'],
                fg="white"
            )
            content.pack(padx=20, pady=14)
            
        else:
            # AI消息 - 左侧对齐
            msg_container.pack_configure(anchor="w")
            
            # 消息内容框架
            content_frame = tk.Frame(msg_container, bg=self.COLORS['bg_dark'])
            content_frame.pack(side=LEFT)
            
            # AI消息气泡 - 深色卡片背景
            bubble = tk.Frame(content_frame, bg=self.COLORS['bg_card'], padx=2, pady=2)
            bubble.pack(side=LEFT, padx=(0, 100))
            
            # 消息文本
            content = tk.Label(
                bubble,
                text=msg.content,
                wraplength=700,
                justify=LEFT,
                font=("Microsoft YaHei", 11),
                bg=self.COLORS['bg_card'],
                fg=self.COLORS['text_primary']
            )
            content.pack(padx=20, pady=14)
        
        self.message_frames.append(msg_container)
        
        # 滚动到底部
        self.message_area.update_idletasks()
        self.message_area.yview_moveto(1.0)
        
    def _send_message(self, event=None):
        """发送消息"""
        content = self.input_text.get("1.0", END).strip()
        
        # 检查是否是占位符或空内容
        if not content or content == "输入您的问题...":
            return
            
        # 清空输入框，保持空白（只保留光标）
        self.input_text.delete("1.0", END)
        self.input_text.config(fg=self.COLORS['text_primary'])
        
        # 添加用户消息
        user_msg = ChatMessage(content, True)
        self.current_conversation.messages.append(user_msg)
        self._add_message_to_display(user_msg)
        
        # 显示输入指示器
        self._show_typing_indicator()
        
        # 判断是草药查询模式还是普通聊天模式
        if self.herb_query_mode:
            # 草药查询模式 - 直接查询Supabase
            threading.Thread(
                target=self._get_herb_response, 
                args=(content,),
                daemon=True
            ).start()
        else:
            # 普通聊天模式 - 先进行意图识别
            # 如果是中药查询，直接查询 Supabase；否则调用 API
            threading.Thread(
                target=self._process_with_intent, 
                args=(content, self.current_conversation.session_id),
                daemon=True
            ).start()
        
    def _show_typing_indicator(self):
        """显示正在输入指示器 - 深色设计"""
        self.typing_frame = tk.Frame(self.message_area, bg=self.COLORS['bg_dark'])
        self.typing_frame.pack(fill=X, pady=16, anchor="w")
        
        # 思考提示气泡 - 深色卡片
        bubble = tk.Frame(self.typing_frame, bg=self.COLORS['bg_card'], padx=2, pady=2)
        bubble.pack(side=LEFT)
        
        self.typing_label = tk.Label(
            bubble,
            text="正在思考...",
            font=("Microsoft YaHei", 11),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_secondary']
        )
        self.typing_label.pack(padx=20, pady=14)
        
        self.message_area.update_idletasks()
        self.message_area.yview_moveto(1.0)
        
    def _get_herb_response(self, drug_name: str):
        """获取草药查询响应（从Supabase）"""
        try:
            # 直接调用API客户端的Supabase查询方法
            result = self.api_client.query_supabase_herb(drug_name)
            
            # 在主线程中更新UI
            self.root.after(0, self._on_herb_response, result)
        except Exception as e:
            self.root.after(0, self._on_herb_response, {
                "success": False,
                "message": f"查询出错：{str(e)}"
            })
    
    def _on_herb_response(self, result: Dict):
        """处理草药查询响应"""
        # 移除输入指示器
        if hasattr(self, 'typing_frame'):
            self.typing_frame.destroy()
        
        if result.get("success"):
            # 查询成功，显示格式化结果
            message = result.get("formatted", result.get("message", ""))
        else:
            # 查询失败
            message = result.get("message", "查询失败")
            
            # 如果有建议的药物，显示出来
            if result.get("suggestions"):
                message += "\n\n您是否想找：\n"
                for suggestion in result.get("suggestions"):
                    message += f"• {suggestion}\n"
                message += "\n请输入完整的药物名称进行查询。"
        
        # 添加系统回复
        response_msg = ChatMessage(message, False)
        self.current_conversation.messages.append(response_msg)
        self._add_message_to_display(response_msg)
        self._scroll_to_bottom()
    
    def _process_with_intent(self, query: str, session_id: Optional[str] = None):
        """
        根据意图处理查询
        如果是中药查询，直接查询 Supabase；否则调用 API
        """
        try:
            # 进行意图识别
            router = QueryRouter()
            route_result = router.route(query)
            
            # 检查是否是中药查询
            if route_result.get("intent") == "herb_query":
                # 中药查询 - 直接查询 Supabase
                print(f"[Intent] 识别为中药查询: {query}")
                
                # 提取草药名称（从实体中获取）
                entities = route_result.get("entities", {})
                herb_names = entities.get("herb", [])
                
                # 如果实体中没有提取到草药名，尝试用 HerbKeywordExtractor 提取
                if not herb_names:
                    try:
                        from core.herb_sql_generator import HerbKeywordExtractor
                        extractor = HerbKeywordExtractor()
                        herb_names = extractor.extract(query)
                        print(f"[Intent] 使用 HerbKeywordExtractor 提取: {herb_names}")
                    except Exception as e:
                        print(f"[Intent] HerbKeywordExtractor 提取失败: {e}")
                
                if herb_names:
                    drug_name = herb_names[0]
                    # 使用 Supabase 客户端查询
                    result = self.api_client.query_supabase_herb(drug_name)
                    self.root.after(0, self._on_herb_response, result)
                else:
                    # 仍然没有识别出草药名，使用查询文本进行模糊搜索
                    print(f"[Intent] 未识别草药名，使用关键词搜索: {query}")
                    # 去除常见停用词后进行搜索
                    search_keyword = self._extract_search_keyword(query)
                    if search_keyword:
                        result = self.api_client.supabase_client.search_shennong_herbs(search_keyword, limit=1)
                        if result:
                            formatted = self.api_client.supabase_client.format_shennong_herb(result[0])
                            response_result = {
                                "success": True,
                                "drug_name": result[0].get("drug_name", ""),
                                "formatted": formatted,
                                "message": f"找到草药：{result[0].get('drug_name', '')}"
                            }
                            self.root.after(0, self._on_herb_response, response_result)
                        else:
                            self.root.after(0, self._on_herb_response, {
                                "success": False,
                                "message": f"未找到与'{query}'相关的草药"
                            })
                    else:
                        self.root.after(0, self._on_herb_response, {
                            "success": False,
                            "message": "请输入草药名称进行查询"
                        })
            else:
                # 其他查询 - 调用 API
                print(f"[Intent] 识别为其他查询: {route_result.get('intent')}")
                self._get_ai_response(query, session_id)
                
        except Exception as e:
            print(f"[Intent] 意图识别失败: {e}")
            # 意图识别失败，回退到 API
            self._get_ai_response(query, session_id)
    
    def _extract_search_keyword(self, query: str) -> str:
        """从查询中提取搜索关键词"""
        # 去除常见停用词
        stop_words = ["的", "功效", "作用", "是什么", "怎么样", "如何", "请", "问", "一下", "查询", "查", "找"]
        keyword = query
        for word in stop_words:
            keyword = keyword.replace(word, "")
        return keyword.strip()
    
    def _format_sql_result(self, result: Dict) -> Dict:
        """格式化 SQL 查询结果为草药查询格式"""
        if not result.get("success"):
            return {
                "success": False,
                "message": result.get("message", result.get("error", "查询失败")),
                "sql": result.get("sql", ""),
                "explanation": result.get("explanation", "")
            }
        
        data = result.get("data")
        if isinstance(data, list):
            if not data:
                return {
                    "success": False,
                    "message": f"未找到相关药物",
                    "sql": result.get("sql", ""),
                    "explanation": result.get("explanation", "")
                }
            data = data[0]
        
        # 格式化药物信息
        formatted = self._format_herb_info_from_sql(data)
        
        return {
            "success": True,
            "drug_name": data.get("drug_name", ""),
            "data": data,
            "formatted": formatted,
            "message": f"找到药物：{data.get('drug_name', '')}",
            "sql": result.get("sql", ""),
            "explanation": result.get("explanation", ""),
            "extracted_herbs": result.get("extracted_herbs", [])
        }
    
    def _format_herb_info_from_sql(self, herb: Dict) -> str:
        """格式化 SQL 查询到的药物信息"""
        lines = []
        lines.append(f"【{herb.get('drug_name', '未知药物')}】")
        lines.append("")
        
        if herb.get('original_text'):
            lines.append("[本经原文]")
            lines.append(self._clean_herb_text(herb['original_text']))
            lines.append("")
        
        if herb.get('properties'):
            lines.append("[性味]")
            lines.append(self._clean_herb_text(herb['properties']))
            lines.append("")
        
        if herb.get('origin'):
            lines.append("[产地]")
            lines.append(self._clean_herb_text(herb['origin']))
            lines.append("")
        
        if herb.get('indications'):
            lines.append("[主治]")
            lines.append(self._clean_herb_text(herb['indications']))
            lines.append("")
        
        if herb.get('dosage'):
            lines.append("[用量]")
            lines.append(self._clean_herb_text(herb['dosage']))
            lines.append("")
        
        if herb.get('contraindications'):
            lines.append("[禁忌]")
            lines.append(self._clean_herb_text(herb['contraindications']))
            lines.append("")
        
        # 添加其他字段（历代医家论述）
        for i in range(1, 12):
            other_name = herb.get(f"other{i}_name")
            other_content = herb.get(f"other{i}")
            if other_name and other_content:
                cleaned_content = self._clean_herb_text(other_content)
                if cleaned_content:
                    lines.append(f"[{other_name}]")
                    lines.append(cleaned_content)
                    lines.append("")
        
        # 添加查询出处
        lines.append("─" * 40)
        lines.append("📚 查询出处：神农本草经")
        lines.append("数据来源：Supabase 数据库")
        
        return "\n".join(lines)
    
    def _extract_herb_name(self, query: str, entities: Dict) -> Optional[str]:
        """从查询中提取中药名称"""
        # 1. 从实体中提取
        herb_entities = entities.get("herb", [])
        if herb_entities:
            return herb_entities[0]
        
        # 2. 从查询中匹配常见中药
        common_herbs = [
            "人参", "黄芪", "当归", "甘草", "桂枝", "麻黄", "柴胡",
            "白术", "茯苓", "川芎", "熟地黄", "白芍", "生姜", "大枣",
            "半夏", "陈皮", "枳实", "厚朴", "大黄", "黄连", "黄芩",
            "黄柏", "栀子", "连翘", "金银花", "薄荷", "防风", "荆芥",
            "丹砂", "朱砂", "石膏", "知母", "麦冬", "天冬", "枸杞子",
            "菊花", "决明子", "牛膝", "杜仲", "续断", "补骨脂", "菟丝子",
            "五味子", "山茱萸", "牡丹皮", "泽泻", "山药", "附子", "干姜",
            "肉桂", "吴茱萸", "细辛", "葛根", "升麻", "白芷", "蔓荆子",
            "桑叶", "菊花", "银柴胡", "地骨皮", "青蒿", "鳖甲", "龟板",
            "龙骨", "牡蛎", "酸枣仁", "柏子仁", "远志", "合欢皮", "夜交藤"
        ]
        
        for herb in common_herbs:
            if herb in query:
                return herb
        
        # 3. 尝试提取可能的药物名称（2-4个字符的中文）
        import re
        # 匹配"XX药"、"XX草"等模式
        patterns = [
            r"([\u4e00-\u9fa5]{2,4})药",
            r"([\u4e00-\u9fa5]{2,4})草",
            r"([\u4e00-\u9fa5]{2,4})根",
            r"([\u4e00-\u9fa5]{2,4})皮",
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return None
    
    def _get_ai_response(self, query: str, session_id: Optional[str] = None):
        """获取AI响应"""
        try:
            # 调用实际API
            result = self.api_client.chat(query, session_id)
            
            # 在主线程中更新UI
            self.root.after(0, self._on_ai_response, result)
        except Exception as e:
            self.root.after(0, self._on_ai_response, {
                "success": False,
                "message": f"发生错误：{str(e)}"
            })
            
    def _on_ai_response(self, result: Dict):
        """处理AI响应"""
        # 移除输入指示器
        if hasattr(self, 'typing_frame'):
            self.typing_frame.destroy()
        
        # 获取消息内容
        message = result.get("message", "抱歉，没有获取到回复")
        
        # 如果有数据源信息，添加到消息中
        if result.get("success") and result.get("sources"):
            sources = result.get("sources", [])
            if sources:
                message += "\n\n**参考来源：**"
                for i, src in enumerate(sources[:3], 1):
                    source_type = src.get("source_type", "未知")
                    message += f"\n{i}. {source_type}"
        
        # 更新会话ID
        if result.get("session_id"):
            self.current_conversation.session_id = result.get("session_id")
        
        # 添加AI消息
        ai_msg = ChatMessage(message, False)
        self.current_conversation.messages.append(ai_msg)
        self._add_message_to_display(ai_msg)
        
    def _on_enter_pressed(self, event):
        """处理回车键"""
        self._send_message()
        return "break"  # 阻止默认换行
        
    def _on_shift_enter(self, event):
        """处理Shift+回车"""
        # 允许换行，不阻止默认行为
        pass
        
    def _new_conversation(self):
        """新建会话"""
        # 退出草药查询模式（普通新会话）
        self._exit_herb_query_mode()
        
        new_id = str(len(self.conversations) + 1)
        new_conv = Conversation(new_id, f"新对话 {new_id}", [])
        self.conversations.insert(0, new_conv)
        self._refresh_conversation_list()
        self._select_conversation(new_conv)
        
    def _quick_herb(self):
        """中药查询快捷入口 - 切换到草药查询模式"""
        self._enter_herb_query_mode()
    
    def _enter_herb_query_mode(self):
        """进入草药查询模式"""
        # 创建新的草药查询会话
        self.herb_query_mode = True
        
        new_conv = Conversation(
            id=str(time.time()),
            title=self.herb_query_title,
            messages=[]
        )
        
        self.conversations.insert(0, new_conv)
        self._refresh_conversation_list()
        self._select_conversation(new_conv)
        
        # 显示草药查询欢迎消息
        welcome_msg = """[已进入草药查询模式]

我可以帮您查询《神农本草经》中的草药信息。

请直接输入草药名称，例如：
- 人参
- 黄芪  
- 丹砂
- 甘草

我会从数据库中查询详细信息并为您展示。"""
        
        self._add_system_message(welcome_msg)
        self._scroll_to_bottom()
    
    def _exit_herb_query_mode(self):
        """退出草药查询模式"""
        self.herb_query_mode = False
        
    def _quick_acupuncture(self):
        """穴位查询快捷入口"""
        self._new_conversation()
        self.input_text.delete("1.0", END)
        self.input_text.config(fg="white")
        self.input_text.insert(END, "请问足三里穴位的定位和主治是什么？")
        self.input_text.focus()
        
    def _quick_formula(self):
        """方剂查询快捷入口"""
        self._new_conversation()
        self.input_text.delete("1.0", END)
        self.input_text.config(fg="white")
        self.input_text.insert(END, "我想了解桂枝汤的组成和功效")
        self.input_text.focus()
        
    def _quick_diagnosis(self):
        """症状诊断快捷入口"""
        self._show_diagnosis()
        
    def _show_diagnosis(self):
        """显示病情诊断界面"""
        dialog = ttkb.Toplevel(self.root)
        dialog.title("病情诊断")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttkb.Label(
            dialog,
            text="智能病情诊断",
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20)
        
        ttkb.Label(
            dialog,
            text="请详细描述您的症状、舌象、脉象等信息：",
            font=("Microsoft YaHei", 12)
        ).pack(pady=10)
        
        # 症状输入
        text_frame = ttkb.Frame(dialog)
        text_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        text = tk.Text(text_frame, height=10, font=("Microsoft YaHei", 11), wrap=WORD)
        text.pack(fill=BOTH, expand=True, side=LEFT)
        
        scrollbar = ttkb.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(fill=Y, side=RIGHT)
        text.config(yscrollcommand=scrollbar.set)
        
        # 结果显示区域
        result_frame = ttkb.LabelFrame(dialog, text="诊断结果", padding=10)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        result_text = tk.Text(result_frame, height=10, font=("Microsoft YaHei", 11), wrap=WORD, state=DISABLED)
        result_text.pack(fill=BOTH, expand=True)
        
        # 进度条
        progress = ttkb.Progressbar(dialog, mode="indeterminate", bootstyle="primary")
        
        def do_diagnosis():
            content = text.get("1.0", END).strip()
            if not content or len(content) < 10:
                messagebox.showwarning("输入不足", "请详细描述您的症状（至少10个字）", parent=dialog)
                return
            
            # 显示进度条
            progress.pack(fill=X, padx=20, pady=10)
            progress.start()
            
            # 禁用按钮
            diagnose_btn.config(state=DISABLED)
            
            def run_diagnosis():
                try:
                    result = self.api_client.diagnose(content)
                    
                    self.root.after(0, lambda: self._show_diagnosis_result(result, result_text, progress, diagnose_btn))
                except Exception as e:
                    self.root.after(0, lambda: self._show_diagnosis_error(str(e), result_text, progress, diagnose_btn))
            
            threading.Thread(target=run_diagnosis, daemon=True).start()
        
        def close_dialog():
            dialog.destroy()
        
        # 按钮区域
        btn_frame = ttkb.Frame(dialog)
        btn_frame.pack(pady=15)
        
        diagnose_btn = ttkb.Button(
            btn_frame,
            text="开始诊断",
            bootstyle="primary",
            command=do_diagnosis,
            width=15
        )
        diagnose_btn.pack(side=LEFT, padx=5)
        
        ttkb.Button(
            btn_frame,
            text="关闭",
            bootstyle="secondary-outline",
            command=close_dialog,
            width=15
        ).pack(side=LEFT, padx=5)
    
    def _show_diagnosis_result(self, result: Dict, result_text: tk.Text, progress: ttkb.Progressbar, btn: ttkb.Button):
        """显示诊断结果"""
        progress.stop()
        progress.pack_forget()
        btn.config(state=NORMAL)
        
        result_text.config(state=NORMAL)
        result_text.delete("1.0", END)
        
        if not result.get("success"):
            result_text.insert(END, f"诊断失败\n\n{result.get('message', '未知错误')}")
            result_text.config(state=DISABLED)
            return
        
        # 格式化诊断结果
        output = f"辨证结果：{result.get('syndrome_type', '未知')}\n\n"
        
        if result.get('pathogenesis'):
            output += f"病机分析\n{result['pathogenesis']}\n\n"
        
        if result.get('treatment_principle'):
            output += f"治则治法\n{result['treatment_principle']}\n\n"
        
        if result.get('recommendations'):
            output += "参考方案\n"
            for i, rec in enumerate(result['recommendations'][:3], 1):
                output += f"\n{i}. {rec.get('name', '方案')}\n"
                output += f"   类型：{rec.get('type', '未知')}\n"
                output += f"   出处：{rec.get('source', '未知')}\n"
            output += "\n"
        
        if result.get('analysis'):
            output += f"详细分析\n{result['analysis']}\n\n"
        
        if result.get('warnings'):
            output += "重要提示\n"
            for warning in result['warnings']:
                output += f"• {warning}\n"
        
        result_text.insert(END, output)
        result_text.config(state=DISABLED)
    
    def _show_diagnosis_error(self, error: str, result_text: tk.Text, progress: ttkb.Progressbar, btn: ttkb.Button):
        """显示诊断错误"""
        progress.stop()
        progress.pack_forget()
        btn.config(state=NORMAL)
        
        result_text.config(state=NORMAL)
        result_text.delete("1.0", END)
        result_text.insert(END, f"诊断出错\n\n{error}")
        result_text.config(state=DISABLED)
        
    def _show_knowledge(self):
        """显示知识查询界面"""
        dialog = ttkb.Toplevel(self.root)
        dialog.title("知识查询")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttkb.Label(
            dialog,
            text="中医知识库",
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20)
        
        # 查询区域
        query_frame = ttkb.Frame(dialog)
        query_frame.pack(fill=X, padx=20, pady=10)
        
        query_entry = ttkb.Entry(query_frame, font=("Microsoft YaHei", 12))
        query_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        query_entry.insert(0, "输入关键词...")
        query_entry.bind("<FocusIn>", lambda e: query_entry.delete(0, END) if query_entry.get() == "输入关键词..." else None)
        
        source_var = ttkb.StringVar(value="全部")
        source_combo = ttkb.Combobox(
            query_frame,
            values=["全部", "acupuncture", "shanghan", "jinkui", "shennong", "cases"],
            textvariable=source_var,
            state="readonly",
            width=15
        )
        source_combo.pack(side=LEFT, padx=5)
        
        # 结果显示区域
        result_frame = ScrolledFrame(dialog, autohide=True)
        result_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        def do_search():
            query = query_entry.get().strip()
            if not query or query == "输入关键词...":
                return
            
            # 清除旧结果
            for widget in result_frame.winfo_children():
                widget.destroy()
            
            # 显示加载中
            loading = ttkb.Label(result_frame, text="搜索中...", font=("Microsoft YaHei", 12))
            loading.pack(pady=20)
            dialog.update()
            
            def run_search():
                result = self.api_client.search_knowledge(query, source_var.get())
                self.root.after(0, lambda: self._show_search_results(result, result_frame))
            
            threading.Thread(target=run_search, daemon=True).start()
        
        search_btn = ttkb.Button(
            query_frame,
            text="搜索",
            bootstyle="primary",
            command=do_search
        )
        search_btn.pack(side=LEFT, padx=5)
        
        # 绑定回车键
        query_entry.bind("<Return>", lambda e: do_search())
        
        ttkb.Button(
            dialog,
            text="关闭",
            bootstyle="secondary-outline",
            command=dialog.destroy,
            width=15
        ).pack(pady=15)
    
    def _show_search_results(self, result: Dict, result_frame: ScrolledFrame):
        """显示搜索结果"""
        # 清除加载提示
        for widget in result_frame.winfo_children():
            widget.destroy()
        
        if not result.get("success"):
            error_label = ttkb.Label(
                result_frame,
                text=f"搜索失败：{result.get('error', '未知错误')}",
                font=("Microsoft YaHei", 12),
                bootstyle="danger"
            )
            error_label.pack(pady=20)
            return
        
        count = result.get("count", 0)
        results = result.get("results", [])
        
        # 显示结果数量
        count_label = ttkb.Label(
            result_frame,
            text=f"找到 {count} 条相关结果",
            font=("Microsoft YaHei", 12, "bold")
        )
        count_label.pack(anchor="w", pady=(0, 10))
        
        # 显示每条结果
        for i, item in enumerate(results, 1):
            item_frame = ttkb.Frame(result_frame, bootstyle="secondary")
            item_frame.pack(fill=X, pady=5, padx=5)
            
            score = item.get("score", 0)
            source = item.get("source", "未知")
            content = item.get("content", "")[:300]
            
            header = ttkb.Label(
                item_frame,
                text=f"结果 {i} | 来源: {source} | 相关度: {score:.2f}",
                font=("Microsoft YaHei", 10, "bold"),
                bootstyle="primary"
            )
            header.pack(anchor="w", padx=10, pady=5)
            
            content_label = ttkb.Label(
                item_frame,
                text=content + "..." if len(item.get("content", "")) > 300 else content,
                font=("Microsoft YaHei", 10),
                wraplength=700,
                justify=LEFT
            )
            content_label.pack(anchor="w", padx=10, pady=5)
        
    def _show_settings(self):
        """显示设置界面"""
        dialog = ttkb.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttkb.Label(
            dialog,
            text="设置",
            font=("Microsoft YaHei", 18, "bold")
        ).pack(pady=20)
        
        # API地址设置
        api_frame = ttkb.LabelFrame(dialog, text="API设置", padding=15)
        api_frame.pack(fill=X, padx=20, pady=10)
        
        ttkb.Label(api_frame, text="API地址：").pack(anchor="w")
        
        api_var = ttkb.StringVar(value=self.api_client.api_url)
        api_entry = ttkb.Entry(api_frame, textvariable=api_var, width=40)
        api_entry.pack(fill=X, pady=5)
        
        def test_connection():
            self.api_client.api_url = api_var.get()
            result = self.api_client.check_health()
            if result.get("status") in ["healthy", "ok"]:
                messagebox.showinfo("连接测试", "连接成功！", parent=dialog)
                self._update_api_status(result)
            else:
                messagebox.showerror("连接测试", f"连接失败：{result.get('message', '未知错误')}", parent=dialog)
        
        ttkb.Button(
            api_frame,
            text="测试连接",
            bootstyle="info-outline",
            command=test_connection
        ).pack(anchor="w", pady=5)
        
        # 主题设置
        theme_frame = ttkb.LabelFrame(dialog, text="外观设置", padding=15)
        theme_frame.pack(fill=X, padx=20, pady=10)
        
        ttkb.Label(theme_frame, text="主题：").pack(anchor="w")
        
        theme_var = ttkb.StringVar(value="darkly")
        theme_combo = ttkb.Combobox(
            theme_frame,
            values=["darkly", "flatly", "superhero", "cyborg", "minty", "pulse"],
            textvariable=theme_var,
            state="readonly",
            width=20
        )
        theme_combo.pack(anchor="w", pady=5)
        
        def change_theme():
            self.style.theme_use(theme_var.get())
            messagebox.showinfo("主题", "主题已更改！", parent=dialog)
        
        ttkb.Button(
            theme_frame,
            text="应用主题",
            bootstyle="primary-outline",
            command=change_theme
        ).pack(anchor="w", pady=5)
        
        # 保存按钮
        def save_settings():
            self.api_client.api_url = api_var.get()
            messagebox.showinfo("保存", "设置已保存！", parent=dialog)
            dialog.destroy()
        
        ttkb.Button(
            dialog,
            text="保存",
            bootstyle="primary",
            command=save_settings,
            width=15
        ).pack(pady=20)
        
    def _show_chat_menu(self):
        """显示聊天菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="重命名", command=self._rename_conversation)
        menu.add_command(label="删除", command=self._delete_conversation)
        menu.add_separator()
        menu.add_command(label="导出对话", command=self._export_conversation)
        
        try:
            menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
        except:
            pass
            
    def _rename_conversation(self):
        """重命名会话"""
        if not self.current_conversation:
            return
            
        dialog = ttkb.Toplevel(self.root)
        dialog.title("重命名")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        entry = ttkb.Entry(dialog, width=30)
        entry.insert(0, self.current_conversation.title)
        entry.pack(pady=20)
        entry.select_range(0, END)
        entry.focus()
        
        def save():
            new_name = entry.get().strip()
            if new_name:
                self.current_conversation.title = new_name
                self._refresh_conversation_list()
            dialog.destroy()
            
        ttkb.Button(dialog, text="保存", command=save, bootstyle="primary").pack()
        
    def _delete_conversation(self):
        """删除会话"""
        if not self.current_conversation:
            return
            
        if messagebox.askyesno("确认", "确定要删除这个对话吗？"):
            self.conversations.remove(self.current_conversation)
            self.current_conversation = None
            self._refresh_conversation_list()
            self._new_conversation()
            
    def _export_conversation(self):
        """导出对话"""
        if not self.current_conversation:
            return
            
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"conversation_{self.current_conversation.id}.txt"
        )
        
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"对话：{self.current_conversation.title}\n")
                    f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for msg in self.current_conversation.messages:
                        role = "用户" if msg.is_user else "助手"
                        f.write(f"[{msg.timestamp}] {role}：\n{msg.content}\n\n")
                
                messagebox.showinfo("导出成功", f"对话已导出到：{filename}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出时发生错误：{str(e)}")


def main():
    """主函数"""
    # 创建窗口
    root = ttkb.Window(themename="darkly")
    
    # 创建应用
    app = TCMChatApp(root)
    
    # 运行
    root.mainloop()


if __name__ == "__main__":
    main()
