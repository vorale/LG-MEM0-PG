#!/usr/bin/env python3
"""
情感陪伴风格配置工具

允许用户选择和配置不同的情感陪伴风格
"""

import os
import sys
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.emotional_prompts import EMOTIONAL_PROMPTS, get_emotional_prompt

def show_available_styles():
    """显示所有可用的情感陪伴风格"""
    print("💝 可用的情感陪伴风格：")
    print("=" * 50)
    
    for i, (key, value) in enumerate(EMOTIONAL_PROMPTS.items(), 1):
        print(f"{i}. 🌟 {value['name']} ({key})")
        print(f"   {value['description']}")
        print()

def preview_style(style_key: str):
    """预览指定风格的提示词"""
    if style_key not in EMOTIONAL_PROMPTS:
        print(f"❌ 风格 '{style_key}' 不存在")
        return
    
    style_info = EMOTIONAL_PROMPTS[style_key]
    prompt = get_emotional_prompt(style_key)
    
    print(f"🎭 风格预览：{style_info['name']}")
    print("=" * 50)
    print(f"📝 描述：{style_info['description']}")
    print("\n📋 提示词内容：")
    print("-" * 30)
    print(prompt)
    print("-" * 30)

def set_emotional_style(style_key: str):
    """设置情感陪伴风格"""
    if style_key not in EMOTIONAL_PROMPTS:
        print(f"❌ 风格 '{style_key}' 不存在")
        return False
    
    # 更新 .env 文件
    env_file = ".env"
    env_lines = []
    style_found = False
    
    # 读取现有的 .env 文件
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('EMOTIONAL_COMPANION_STYLE='):
                    env_lines.append(f'EMOTIONAL_COMPANION_STYLE={style_key}\n')
                    style_found = True
                else:
                    env_lines.append(line)
    
    # 如果没有找到配置项，添加新的
    if not style_found:
        env_lines.append(f'EMOTIONAL_COMPANION_STYLE={style_key}\n')
    
    # 写回 .env 文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(env_lines)
    
    style_info = EMOTIONAL_PROMPTS[style_key]
    print(f"✅ 情感陪伴风格已设置为：{style_info['name']}")
    print(f"📝 描述：{style_info['description']}")
    print("\n🔄 请重启API服务以应用新的风格设置")
    
    return True

def get_current_style():
    """获取当前设置的风格"""
    # 从环境变量获取
    current_style = os.getenv('EMOTIONAL_COMPANION_STYLE', 'warm_friend')
    
    # 从 .env 文件获取
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('EMOTIONAL_COMPANION_STYLE='):
                    current_style = line.split('=', 1)[1].strip()
                    break
    
    return current_style

def interactive_style_selection():
    """交互式风格选择"""
    print("🎭 情感陪伴风格配置向导")
    print("=" * 40)
    
    # 显示当前风格
    current_style = get_current_style()
    if current_style in EMOTIONAL_PROMPTS:
        current_name = EMOTIONAL_PROMPTS[current_style]['name']
        print(f"📍 当前风格：{current_name} ({current_style})")
    else:
        print(f"📍 当前风格：{current_style} (可能是自定义风格)")
    
    print()
    show_available_styles()
    
    while True:
        try:
            choice = input("请选择风格 (输入数字 1-5，或输入风格key，或 'q' 退出): ").strip()
            
            if choice.lower() == 'q':
                print("👋 退出配置")
                break
            
            # 如果输入的是数字
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(EMOTIONAL_PROMPTS):
                    style_key = list(EMOTIONAL_PROMPTS.keys())[choice_num - 1]
                else:
                    print("❌ 请输入有效的数字 (1-5)")
                    continue
            else:
                # 如果输入的是风格key
                style_key = choice
            
            if style_key not in EMOTIONAL_PROMPTS:
                print(f"❌ 风格 '{style_key}' 不存在，请重新选择")
                continue
            
            # 预览风格
            print(f"\n🔍 预览风格：{EMOTIONAL_PROMPTS[style_key]['name']}")
            preview_choice = input("是否查看完整预览？(y/N): ").strip().lower()
            if preview_choice == 'y':
                preview_style(style_key)
            
            # 确认设置
            confirm = input(f"\n确认设置为 '{EMOTIONAL_PROMPTS[style_key]['name']}' 风格？(y/N): ").strip().lower()
            if confirm == 'y':
                if set_emotional_style(style_key):
                    break
            else:
                print("❌ 已取消设置")
                
        except KeyboardInterrupt:
            print("\n👋 退出配置")
            break
        except Exception as e:
            print(f"❌ 发生错误：{e}")

def test_current_style():
    """测试当前风格的提示词"""
    current_style = get_current_style()
    
    print(f"🧪 测试当前风格：{current_style}")
    print("=" * 40)
    
    if current_style in EMOTIONAL_PROMPTS:
        style_info = EMOTIONAL_PROMPTS[current_style]
        print(f"📝 风格名称：{style_info['name']}")
        print(f"📋 风格描述：{style_info['description']}")
        
        # 显示提示词的关键特征
        prompt = get_emotional_prompt(current_style)
        lines = prompt.split('\n')
        
        print("\n🎯 提示词关键特征：")
        for line in lines[:10]:  # 显示前10行
            if line.strip():
                print(f"   {line}")
        
        if len(lines) > 10:
            print(f"   ... (还有 {len(lines) - 10} 行)")
    else:
        print(f"⚠️  风格 '{current_style}' 可能是自定义风格或不存在")

def create_custom_style():
    """创建自定义风格（高级功能）"""
    print("🎨 创建自定义情感陪伴风格")
    print("=" * 40)
    print("这是一个高级功能，需要手动编辑 emotional_companion_prompts.py 文件")
    print("\n📝 步骤：")
    print("1. 打开 emotional_companion_prompts.py 文件")
    print("2. 在 EMOTIONAL_PROMPTS 字典中添加新的风格")
    print("3. 定义风格的 name、prompt 和 description")
    print("4. 保存文件并重启服务")
    print("\n💡 建议先复制现有风格作为模板进行修改")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="情感陪伴风格配置工具")
    parser.add_argument("--list", action="store_true", help="显示所有可用风格")
    parser.add_argument("--current", action="store_true", help="显示当前风格")
    parser.add_argument("--set", help="设置指定风格")
    parser.add_argument("--preview", help="预览指定风格")
    parser.add_argument("--test", action="store_true", help="测试当前风格")
    parser.add_argument("--interactive", action="store_true", help="交互式选择风格")
    parser.add_argument("--custom", action="store_true", help="创建自定义风格指南")
    
    args = parser.parse_args()
    
    if args.list:
        show_available_styles()
    elif args.current:
        current_style = get_current_style()
        if current_style in EMOTIONAL_PROMPTS:
            style_info = EMOTIONAL_PROMPTS[current_style]
            print(f"📍 当前风格：{style_info['name']} ({current_style})")
            print(f"📝 描述：{style_info['description']}")
        else:
            print(f"📍 当前风格：{current_style}")
    elif args.set:
        set_emotional_style(args.set)
    elif args.preview:
        preview_style(args.preview)
    elif args.test:
        test_current_style()
    elif args.interactive:
        interactive_style_selection()
    elif args.custom:
        create_custom_style()
    else:
        print("💝 情感陪伴风格配置工具")
        print("\n使用方法：")
        print("  --list         显示所有可用风格")
        print("  --current      显示当前风格")
        print("  --set STYLE    设置指定风格")
        print("  --preview STYLE 预览指定风格")
        print("  --test         测试当前风格")
        print("  --interactive  交互式选择风格")
        print("  --custom       创建自定义风格指南")
        print("\n快速开始：")
        print("  python configure_emotional_style.py --interactive")
