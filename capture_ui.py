#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截取UI预览图
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
from PIL import ImageGrab
import time

def capture_ui():
    # 创建窗口
    root = ttkb.Window(themename='darkly')
    root.title('中医智能助手')
    root.geometry('1200x800')

    # 主容器
    main_container = ttkb.Frame(root)
    main_container.pack(fill=BOTH, expand=True)

    # 左侧边栏
    sidebar = ttkb.Frame(main_container, width=280)
    sidebar.pack(side=LEFT, fill=Y)
    sidebar.pack_propagate(False)

    # 顶部标题
    header = ttkb.Frame(sidebar)
    header.pack(fill=X, padx=15, pady=15)
    title_label = ttkb.Label(header, text='中医智能助手', font=('Microsoft YaHei', 14, 'bold'), bootstyle='primary')
    title_label.pack(side=LEFT)
    new_btn = ttkb.Button(header, text='+', width=3, bootstyle='primary-outline')
    new_btn.pack(side=RIGHT)

    # API状态
    api_status_frame = ttkb.Frame(sidebar)
    api_status_frame.pack(fill=X, padx=15, pady=(0, 5))
    api_status_label = ttkb.Label(api_status_frame, text='服务正常', font=('Microsoft YaHei', 9), bootstyle='success')
    api_status_label.pack(side=LEFT)

    # 搜索框
    search_frame = ttkb.Frame(sidebar)
    search_frame.pack(fill=X, padx=15, pady=(0, 10))
    search_entry = ttkb.Entry(search_frame, bootstyle='secondary')
    search_entry.pack(fill=X)
    search_entry.insert(0, '搜索对话...')

    # 会话列表
    conv_list = ScrolledFrame(sidebar, autohide=True)
    conv_list.pack(fill=BOTH, expand=True, padx=10, pady=5)

    # 添加示例会话
    for i in range(3):
        btn = ttkb.Button(conv_list, text=f'对话 {i+1}', bootstyle='secondary-outline')
        btn.pack(fill=X, padx=5, pady=2)

    # 快捷查询区域
    quick_frame = ttkb.LabelFrame(sidebar, text='快捷查询')
    quick_frame.pack(fill=X, padx=15, pady=(5, 10))
    quick_btn_container = ttkb.Frame(quick_frame)
    quick_btn_container.pack(fill=X, padx=10, pady=10)

    quick_buttons = ['穴位查询', '中药查询', '方剂查询', '症状诊断']
    for text in quick_buttons:
        btn = ttkb.Button(quick_btn_container, text=text, bootstyle='info-outline')
        btn.pack(fill=X, pady=3)

    # 底部按钮
    bottom_frame = ttkb.Frame(sidebar)
    bottom_frame.pack(fill=X, padx=15, pady=5)
    for text in ['知识查询', '设置']:
        btn = ttkb.Button(bottom_frame, text=text, bootstyle='secondary-outline')
        btn.pack(fill=X, pady=2)

    # 右侧聊天区域
    chat_container = ttkb.Frame(main_container)
    chat_container.pack(side=LEFT, fill=BOTH, expand=True)

    # 顶部标题栏
    header_container = ttkb.Frame(chat_container, bootstyle='secondary')
    header_container.pack(fill=X)
    chat_header = ttkb.Frame(header_container, height=55)
    chat_header.pack(fill=X, padx=20, pady=8)
    chat_header.pack_propagate(False)
    chat_title = ttkb.Label(chat_header, text='新建对话', font=('Microsoft YaHei', 14, 'bold'))
    chat_title.pack(side=LEFT, pady=5)
    more_btn = ttkb.Button(chat_header, text='...', width=3, bootstyle='secondary-outline')
    more_btn.pack(side=RIGHT, pady=5)

    # 消息区域
    msg_area = ScrolledFrame(chat_container, autohide=True)
    msg_area.pack(fill=BOTH, expand=True, padx=10, pady=5)

    # 添加欢迎消息
    welcome_frame = ttkb.Frame(msg_area)
    welcome_frame.pack(fill=X, pady=8, padx=15, anchor='w')
    avatar_bg = ttkb.Frame(welcome_frame, bootstyle='primary')
    avatar_bg.pack(side=LEFT, padx=(0, 8))
    avatar = ttkb.Label(avatar_bg, text='AI', font=('Microsoft YaHei', 18), bootstyle='inverse-primary')
    avatar.pack(padx=6, pady=6)
    content_frame = ttkb.Frame(welcome_frame)
    content_frame.pack(side=LEFT)
    bubble = ttkb.Frame(content_frame, bootstyle='secondary')
    bubble.pack(side=LEFT, padx=(0, 60))
    welcome_text = '''欢迎使用中医智能助手！

[针灸穴位查询] 查询经络穴位定位、主治功效
[中药知识] 了解中药性味、功效、用法用量
[经典方剂] 查询伤寒论、金匮要略等经典方剂
[病情诊断] 基于症状的初步辨证分析

使用提示
- 直接输入您的问题
- 点击左侧快捷按钮快速查询
- 使用症状诊断进行详细的病情分析

免责声明
本系统提供的信息仅供参考学习，不能替代专业医生的诊断和治疗建议。'''
    content = ttkb.Label(bubble, text=welcome_text, wraplength=550, justify=LEFT, font=('Microsoft YaHei', 11))
    content.pack(padx=12, pady=10)
    time_label = ttkb.Label(content_frame, text='14:48', font=('Microsoft YaHei', 8), bootstyle='muted')
    time_label.pack(side=LEFT, padx=5, pady=(2, 0))

    # 输入区域
    input_outer = ttkb.Frame(chat_container, bootstyle='secondary')
    input_outer.pack(fill=X, padx=0, pady=0)
    input_container = ttkb.Frame(input_outer)
    input_container.pack(fill=X, padx=20, pady=15)
    input_frame = ttkb.Frame(input_container, bootstyle='dark')
    input_frame.pack(fill=X, expand=True)
    input_text = tk.Text(input_frame, height=3, font=('Microsoft YaHei', 12), bg='#3d3d3d', fg='#888888', insertbackground='white', relief=FLAT, wrap=WORD, padx=12, pady=10)
    input_text.pack(side=LEFT, fill=BOTH, expand=True, padx=2, pady=2)
    input_text.insert('1.0', '输入您的问题...')
    send_btn = ttkb.Button(input_frame, text='发送', bootstyle='primary', width=10)
    send_btn.pack(side=RIGHT, padx=8, pady=8)

    # 更新并截图
    root.update_idletasks()
    time.sleep(0.5)

    # 获取窗口位置并截图
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()
    screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
    screenshot.save('ui_preview.png')
    print('截图已保存到 ui_preview.png')

    root.destroy()

if __name__ == '__main__':
    capture_ui()
