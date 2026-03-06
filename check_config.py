#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置诊断脚本 - 检查 Supabase 配置问题
"""

import os
import sys

print("=" * 60)
print("Supabase 配置诊断")
print("=" * 60)

# 1. 检查当前工作目录
print(f"\n[1] 当前工作目录: {os.getcwd()}")

# 2. 检查 .env 文件位置
possible_paths = [
    ".env",
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
]

print("\n[2] 检查 .env 文件:")
for path in possible_paths:
    exists = os.path.exists(path)
    print(f"  {'✓' if exists else '✗'} {path}")
    if exists:
        print(f"    文件大小: {os.path.getsize(path)} bytes")

# 3. 检查环境变量
print("\n[3] 当前环境变量:")
url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")

print(f"  SUPABASE_URL: {'✓ 已设置' if url else '✗ 未设置'}")
if url:
    print(f"    值: {url[:30]}...")

print(f"  SUPABASE_KEY: {'✓ 已设置' if key else '✗ 未设置'}")
if key:
    print(f"    值: {key[:20]}...")

# 4. 尝试加载 dotenv
print("\n[4] 尝试加载 .env 文件:")
try:
    from dotenv import load_dotenv
    
    # 尝试多个路径
    loaded = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"  尝试加载: {path}")
            load_dotenv(path, override=True)
            loaded = True
            break
    
    if not loaded:
        print("  ✗ 未找到 .env 文件")
    else:
        # 重新检查环境变量
        url_after = os.getenv("SUPABASE_URL", "")
        key_after = os.getenv("SUPABASE_KEY", "")
        
        print(f"  加载后 SUPABASE_URL: {'✓' if url_after else '✗'}")
        print(f"  加载后 SUPABASE_KEY: {'✓' if key_after else '✗'}")
        
except ImportError:
    print("  ✗ python-dotenv 未安装")
    print("    请运行: pip install python-dotenv")

# 5. 检查 .env 文件内容
print("\n[5] .env 文件内容检查:")
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    supabase_lines = [l for l in lines if 'SUPABASE' in l and not l.strip().startswith('#')]
    if supabase_lines:
        print(f"  找到 {len(supabase_lines)} 行 Supabase 配置:")
        for line in supabase_lines:
            print(f"    {line.strip()}")
    else:
        print("  ✗ 未找到 Supabase 相关配置")
        print("  文件内容:")
        for i, line in enumerate(lines[:20], 1):
            print(f"    {i}: {line.strip()}")
else:
    print("  ✗ .env 文件不存在")

print("\n" + "=" * 60)
print("诊断建议:")
print("=" * 60)

if not url and not key:
    print("""
问题: 环境变量未设置

解决方案:
1. 确保 .env 文件存在 (不是 .env.example!)
   复制命令: copy .env.example .env

2. 编辑 .env 文件，添加配置:
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-publishable-key

3. 确保 .env 文件保存在项目根目录

4. 如果使用 VS Code，重启终端使环境变量生效
""")

print("\n按 Enter 退出...")
input()
