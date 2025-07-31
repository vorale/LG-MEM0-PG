#!/usr/bin/env python3
"""
Deployment script for Aurora Serverless infrastructure
Handles CDK deployment and post-deployment configuration
"""

import os
import sys
import subprocess
import json
import boto3
import psycopg2
from dotenv import load_dotenv

def run_command(command, description):
    """Run shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def install_cdk_dependencies():
    """Install CDK dependencies"""
    print("📦 Installing CDK dependencies...")
    
    # Install CDK CLI if not present
    try:
        subprocess.run(["cdk", "--version"], check=True, capture_output=True)
        print("✅ CDK CLI already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing CDK CLI...")
        run_command("npm install -g aws-cdk", "CDK CLI installation")
    
    # Install Python dependencies
    run_command("pip install -r requirements-cdk.txt", "Python CDK dependencies installation")

def bootstrap_cdk():
    """Bootstrap CDK in the current AWS account/region"""
    print("🚀 Bootstrapping CDK...")
    
    # Get current AWS account and region
    try:
        sts = boto3.client('sts', region_name='us-west-2')
        account = sts.get_caller_identity()['Account']
        region = 'us-west-2'  # Force us-west-2 region
        
        print(f"Account: {account}")
        print(f"Region: {region}")
        
        # Bootstrap CDK
        bootstrap_cmd = f"JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1 cdk bootstrap aws://{account}/{region}"
        run_command(bootstrap_cmd, "CDK bootstrap")
        
    except Exception as e:
        print(f"❌ Failed to bootstrap CDK: {e}")
        return False
    
    return True

def deploy_stack():
    """Deploy the Aurora Serverless stack"""
    print("🏗️  Deploying Aurora Serverless stack...")
    
    # Deploy stack
    deploy_cmd = "JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1 cdk deploy LangGraphMem0AuroraStack --require-approval never"
    output = run_command(deploy_cmd, "Stack deployment")
    
    if output is None:
        return None
    
    # Extract outputs from deployment
    try:
        # Get stack outputs
        cloudformation = boto3.client('cloudformation', region_name='us-west-2')
        response = cloudformation.describe_stacks(StackName='LangGraphMem0AuroraStack')
        
        outputs = {}
        if response['Stacks']:
            stack_outputs = response['Stacks'][0].get('Outputs', [])
            for output in stack_outputs:
                outputs[output['OutputKey']] = output['OutputValue']
        
        return outputs
    
    except Exception as e:
        print(f"⚠️  Could not retrieve stack outputs: {e}")
        return {}

def setup_pgvector_extension(outputs):
    """Set up pgvector extension in the Aurora cluster"""
    print("🧠 Setting up pgvector extension...")
    
    try:
        # Get database connection details
        cluster_endpoint = outputs.get('AuroraClusterEndpoint')
        secret_arn = outputs.get('DatabaseSecretArn')
        database_name = outputs.get('DatabaseName', 'mem0_agent')
        
        if not cluster_endpoint or not secret_arn:
            print("❌ Missing required connection details from stack outputs")
            return False
        
        # Get credentials from Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name='us-west-2')
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(secret_response['SecretString'])
        
        # Connect to database
        print(f"Connecting to {cluster_endpoint}...")
        conn = psycopg2.connect(
            host=cluster_endpoint,
            port=5432,
            database=database_name,
            user=secret_data['username'],
            password=secret_data['password'],
            sslmode='require',
            connect_timeout=30
        )
        
        with conn.cursor() as cursor:
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Verify extension is installed
            cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ pgvector extension enabled successfully (version: {result[1]})")
            else:
                print("❌ Failed to enable pgvector extension")
                return False
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up pgvector: {e}")
        return False

def update_env_file(outputs):
    """Update .env file with Aurora connection details"""
    print("📝 Updating .env file with Aurora connection details...")
    
    try:
        # Get database connection details
        cluster_endpoint = outputs.get('AuroraClusterEndpoint')
        cluster_port = outputs.get('AuroraClusterPort', '5432')
        database_name = outputs.get('DatabaseName', 'mem0_agent')
        secret_arn = outputs.get('DatabaseSecretArn')
        
        if not cluster_endpoint:
            print("❌ Missing cluster endpoint from stack outputs")
            return False
        
        # Get credentials from Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name='us-west-2')
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(secret_response['SecretString'])
        
        # Read current .env file
        env_content = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_content = f.readlines()
        
        # Update or add Aurora configuration
        aurora_config = {
            'POSTGRES_HOST': cluster_endpoint,
            'POSTGRES_PORT': cluster_port,
            'POSTGRES_USER': secret_data['username'],
            'POSTGRES_PASSWORD': secret_data['password'],
            'POSTGRES_DB': database_name,
            'POSTGRES_SSL_MODE': 'require',
            'POSTGRES_CONNECT_TIMEOUT': '30',
            'POSTGRES_APPLICATION_NAME': 'langgraph-mem0-agent'
        }
        
        # Create new .env content
        new_env_content = []
        updated_keys = set()
        
        for line in env_content:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0]
                if key in aurora_config:
                    new_env_content.append(f"{key}={aurora_config[key]}\n")
                    updated_keys.add(key)
                else:
                    new_env_content.append(line + '\n')
            else:
                new_env_content.append(line + '\n')
        
        # Add any missing Aurora configuration
        for key, value in aurora_config.items():
            if key not in updated_keys:
                new_env_content.append(f"{key}={value}\n")
        
        # Write updated .env file
        with open('.env', 'w') as f:
            f.writelines(new_env_content)
        
        print("✅ .env file updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Aurora Serverless Deployment for LangGraph + Mem0 Agent")
    print("=" * 60)
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials found for account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials not available: {e}")
        print("Please configure AWS credentials using 'aws configure'")
        sys.exit(1)
    
    # Install dependencies
    install_cdk_dependencies()
    
    # Bootstrap CDK
    if not bootstrap_cdk():
        print("❌ CDK bootstrap failed")
        sys.exit(1)
    
    # Deploy stack
    outputs = deploy_stack()
    if outputs is None:
        print("❌ Stack deployment failed")
        sys.exit(1)
    
    print("\n📋 Stack Outputs:")
    for key, value in outputs.items():
        print(f"  {key}: {value}")
    
    # Set up pgvector extension
    if not setup_pgvector_extension(outputs):
        print("⚠️  pgvector setup failed - you may need to set it up manually")
    
    # Update .env file
    if not update_env_file(outputs):
        print("⚠️  .env file update failed - you may need to update it manually")
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📝 Next steps:")
    print("1. Verify your .env file has been updated with Aurora connection details")
    print("2. Test the connection: python setup_postgres.py")
    print("3. Run the agent: python langgraph_mem0_agent.py")
    print("\n💡 To destroy the infrastructure later: cdk destroy LangGraphMem0AuroraStack")

if __name__ == "__main__":
    main()
