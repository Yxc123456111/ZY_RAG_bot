#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 配置诊断工具
运行此脚本检查配置问题
"""

import os
import sys
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def main():
    print_section("Supabase 配置诊断工具")
    
    # 1. 检查当前目录
    cwd = Path(os.getcwd())
    print(f"\n当前工作目录: {cwd}")
    
    # 2. 检查 .env 文件
    print_section("检查 .env 文件")
    
    env_paths = [
        cwd / ".env",
        Path(__file__).parent / ".env",
    ]
    
    env_found = False
    for env_path in env_paths:
        print(f"\n检查: {env_path}")
        if env_path.exists():
            print(f"  ✓ 文件存在 (大小: {env_path.stat().st_size} bytes)")
            env_found = True
            
            # 读取内容
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查 Supabase 配置
            if 'SUPABASE_URL' in content:
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('SUPABASE_URL') and not line.strip().startswith('#'):
                        print(f"  ✓ 找到 SUPABASE_URL: {line.strip()}")
                    if line.strip().startswith('SUPABASE_KEY') and not line.strip().startswith('#'):
                        key_value = line.strip().split('=', 1)[1] if '=' in line else ""
                        masked = key_value[:10] + "..." if len(key_value) > 10 else key_value
                        print(f"  ✓ 找到 SUPABASE_KEY: {masked}")
            else:
                print(f"  ✗ 未找到 SUPABASE_URL 配置")
                print(f"\n  文件内容预览:")
                lines = content.split('\n')[:10]
                for i, line in enumerate(lines, 1):
                    print(f"    {i}: {line}")
        else:
            print(f"  ✗ 文件不存在")
    
    if not env_found:
        print("\n" + "!" * 60)
        print("错误: 未找到 .env 文件！")
        print("!" * 60)
        print("\n解决方案:")
        print("1. 复制 .env.example 到 .env:")
        print("   copy .env.example .env")
        print("\n2. 编辑 .env 文件，添加 Supabase 配置:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_KEY=your-publishable-key")
        return
    
    # 3. 测试配置管理器
    print_section("测试配置管理器")
    try:
        from config_manager import get_config, is_supabase_ready, get_supabase_url, get_supabase_key
        
        config = get_config()
        print("✓ 配置管理器导入成功")
        
        root = config._get_project_root()
        print(f"✓ 项目根目录: {root}")
        
        url = get_supabase_url()
        key = get_supabase_key()
        
        if url and key:
            print(f"✓ SUPABASE_URL: {url[:30]}...")
            print(f"✓ SUPABASE_KEY: {key[:15]}...")
            print("\n✅ 配置正确！可以正常使用中药查询功能。")
        else:
            print(f"✗ SUPABASE_URL: {'未设置' if not url else '已设置'}")
            print(f"✗ SUPABASE_KEY: {'未设置' if not key else '已设置'}")
            print("\n❌ 配置不完整！请检查 .env 文件。")
            
    except Exception as e:
        print(f"✗ 配置管理器错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 测试 Supabase 客户端
    print_section("测试 Supabase 客户端")
    try:
        from supabase_herb_client import SupabaseHerbClient
        from config_manager import get_supabase_url, get_supabase_key
        
        url = get_supabase_url()
        key = get_supabase_key()
        
        if url and key:
            client = SupabaseHerbClient(url, key)
            print("✓ SupabaseHerbClient 创建成功")
            
            # 尝试查询
            print("\n尝试查询 '人参'...")
            result = client.query_by_name("人参")
            if result:
                print(f"✓ 查询成功: {result.get('drug_name')}")
            else:
                print("✗ 未找到数据（请确认数据库已导入）")
        else:
            print("✗ 跳过测试（配置不完整）")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print_section("诊断完成")
    print("\n如有问题，请查看 QUICK_START_SUPABASE.md")
    input("\n按 Enter 退出...")

if __name__ == "__main__":
    main()
