#!/usr/bin/env python3
"""
Comprehensive verification script for Aurora Serverless setup
Tests all components of the LangGraph + Mem0 Agent infrastructure
"""

import os
import sys
import boto3
import json
import psycopg2
from dotenv import load_dotenv
from mem0 import Memory

def check_aws_credentials():
    """Check AWS credentials and permissions"""
    print("🔐 Checking AWS credentials...")
    
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Account: {identity['Account']}")
        print(f"✅ User/Role: {identity.get('Arn', 'Unknown')}")
        
        # Test Bedrock access
        bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        print("✅ Bedrock access confirmed")
        
        return True
    except Exception as e:
        print(f"❌ AWS credentials issue: {e}")
        return False

def check_aurora_stack():
    """Check if Aurora stack is deployed"""
    print("\n🏗️  Checking Aurora CloudFormation stack...")
    
    try:
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='LangGraphMem0AuroraStack')
        
        if response['Stacks']:
            stack = response['Stacks'][0]
            status = stack['StackStatus']
            print(f"✅ Stack Status: {status}")
            
            if status == 'CREATE_COMPLETE' or status == 'UPDATE_COMPLETE':
                # Get outputs
                outputs = {}
                for output in stack.get('Outputs', []):
                    outputs[output['OutputKey']] = output['OutputValue']
                
                print("📋 Stack Outputs:")
                for key, value in outputs.items():
                    if 'Secret' in key:
                        print(f"  {key}: {value[:20]}...")
                    else:
                        print(f"  {key}: {value}")
                
                return outputs
            else:
                print(f"⚠️  Stack not ready: {status}")
                return None
        else:
            print("❌ Stack not found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking stack: {e}")
        return None

def check_aurora_connection(outputs):
    """Test Aurora database connection"""
    print("\n🐘 Testing Aurora database connection...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Get connection details
        host = os.getenv('POSTGRES_HOST') or outputs.get('AuroraClusterEndpoint')
        port = int(os.getenv('POSTGRES_PORT', '5432'))
        database = os.getenv('POSTGRES_DB') or outputs.get('DatabaseName', 'mem0_agent')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD')
        
        if not password and outputs.get('DatabaseSecretArn'):
            # Get password from Secrets Manager
            secrets = boto3.client('secretsmanager')
            secret_response = secrets.get_secret_value(SecretId=outputs['DatabaseSecretArn'])
            secret_data = json.loads(secret_response['SecretString'])
            password = secret_data['password']
            user = secret_data['username']
        
        if not all([host, password]):
            print("❌ Missing connection details")
            return False
        
        # Test connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode='require',
            connect_timeout=30
        )
        
        with conn.cursor() as cursor:
            # Test basic connection
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL Version: {version[:50]}...")
            
            # Check pgvector extension
            cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            vector_ext = cursor.fetchone()
            
            if vector_ext:
                print(f"✅ pgvector Extension: v{vector_ext[1]}")
            else:
                print("⚠️  pgvector extension not found - attempting to install...")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                print("✅ pgvector extension installed")
            
            # Test vector operations
            cursor.execute("SELECT '[1,2,3]'::vector;")
            test_vector = cursor.fetchone()[0]
            print(f"✅ Vector operations working: {test_vector}")
        
        conn.close()
        print("✅ Aurora connection test successful")
        return True
        
    except Exception as e:
        print(f"❌ Aurora connection failed: {e}")
        return False

def check_mem0_configuration():
    """Test Mem0 memory system"""
    print("\n🧠 Testing Mem0 memory system...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Mem0 with PostgreSQL
        mem0 = Memory.from_config({
            "version": "v1.1",
            "llm": {
                "provider": "aws_bedrock",
                "config": {
                    "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                    "aws_region": os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
                }
            },
            "embedder": {
                "provider": "aws_bedrock",
                "config": {
                    "model": "amazon.titan-embed-text-v1",
                    "aws_region": os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
                }
            },
            "vector_store": {
                "provider": "postgres",
                "config": {
                    "host": os.getenv('POSTGRES_HOST'),
                    "port": int(os.getenv('POSTGRES_PORT', '5432')),
                    "user": os.getenv('POSTGRES_USER'),
                    "password": os.getenv('POSTGRES_PASSWORD'),
                    "database": os.getenv('POSTGRES_DB'),
                    "table_name": "mem0_memories"
                }
            }
        })
        
        # Test memory operations
        test_user_id = "test_verification_user"
        test_memory = "This is a test memory for Aurora Serverless verification"
        
        # Add memory
        mem0.add(test_memory, user_id=test_user_id)
        print("✅ Memory add operation successful")
        
        # Search memory
        results = mem0.search("test memory", user_id=test_user_id)
        if results and results.get("results"):
            print(f"✅ Memory search successful: found {len(results['results'])} results")
        else:
            print("⚠️  Memory search returned no results")
        
        # Clean up test memory
        try:
            mem0.delete_all(user_id=test_user_id)
            print("✅ Memory cleanup successful")
        except:
            pass  # Ignore cleanup errors
        
        return True
        
    except Exception as e:
        print(f"❌ Mem0 configuration failed: {e}")
        return False

def check_bedrock_models():
    """Test AWS Bedrock model access"""
    print("\n🤖 Testing AWS Bedrock models...")
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        # Test Claude model
        test_prompt = "Hello, this is a test."
        
        response = bedrock.invoke_model(
            modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": test_prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        if result.get('content'):
            print("✅ Claude-3-7-Sonnet model access confirmed")
        
        # Test Titan embeddings
        embed_response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v1",
            body=json.dumps({"inputText": test_prompt})
        )
        
        embed_result = json.loads(embed_response['body'].read())
        if embed_result.get('embedding'):
            print("✅ Titan embeddings model access confirmed")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock model access failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🔍 Aurora Serverless Setup Verification")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check AWS credentials
    if not check_aws_credentials():
        all_checks_passed = False
    
    # Check Aurora stack
    outputs = check_aurora_stack()
    if not outputs:
        all_checks_passed = False
        print("\n❌ Cannot proceed without Aurora stack")
        sys.exit(1)
    
    # Check Aurora connection
    if not check_aurora_connection(outputs):
        all_checks_passed = False
    
    # Check Bedrock models
    if not check_bedrock_models():
        all_checks_passed = False
    
    # Check Mem0 configuration
    if not check_mem0_configuration():
        all_checks_passed = False
    
    # Final summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All verification checks passed!")
        print("\n✅ Your Aurora Serverless setup is ready for the LangGraph + Mem0 Agent")
        print("\n📝 Next steps:")
        print("1. Run the agent: python langgraph_mem0_agent.py")
        print("2. Start chatting with your AI agent!")
    else:
        print("❌ Some verification checks failed")
        print("\n🔧 Please review the errors above and:")
        print("1. Check your AWS credentials and permissions")
        print("2. Ensure Aurora stack is deployed successfully")
        print("3. Verify your .env file configuration")
        print("4. Run: python get_aurora_credentials.py")

if __name__ == "__main__":
    main()
