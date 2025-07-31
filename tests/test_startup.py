#!/usr/bin/env python3
"""
简单的启动测试脚本
验证环境变量和数据库连接是否正常
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """测试环境变量加载"""
    print("🧪 测试环境变量加载...")
    
    # 加载.env文件
    load_dotenv()
    
    required_vars = [
        'POSTGRES_HOST',
        'POSTGRES_PORT', 
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        return False
    
    print("✅ 所有环境变量已正确加载")
    return True

def test_postgres_connection():
    """测试PostgreSQL连接"""
    print("\n🧪 测试PostgreSQL连接...")
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB')
        )
        
        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ PostgreSQL版本: {version}")
        
        cursor.close()
        conn.close()
        
        print("✅ PostgreSQL连接成功")
        return True
        
    except ImportError:
        print("❌ psycopg2模块未安装")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        return False

def test_service_import():
    """测试服务导入"""
    print("\n🧪 测试服务导入...")
    
    try:
        from src.api.service import app
        print("   ✅ API服务导入成功")
        
        from src.core.memory_manager import Mem0MemoryManager
        print("   ✅ 记忆管理器导入成功")
        
        from src.core.emotional_prompts import get_emotional_prompt
        print("   ✅ 情感陪伴提示词导入成功")
        
        print("✅ 所有服务模块导入成功")
        return True
        
    except Exception as e:
        print(f"❌ 服务导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 启动环境测试")
    print("=" * 40)
    
    # 测试环境变量
    env_ok = test_environment()
    
    # 测试PostgreSQL连接
    postgres_ok = test_postgres_connection()
    
    # 测试服务导入
    service_ok = test_service_import()
    
    # 总结
    print("\n" + "=" * 40)
    print("📊 测试结果总结:")
    print(f"   环境变量: {'✅ 通过' if env_ok else '❌ 失败'}")
    print(f"   PostgreSQL: {'✅ 通过' if postgres_ok else '❌ 失败'}")
    print(f"   服务导入: {'✅ 通过' if service_ok else '❌ 失败'}")
    
    if env_ok and postgres_ok and service_ok:
        print("\n🎉 所有测试通过！可以启动API服务")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
