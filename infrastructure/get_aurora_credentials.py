#!/usr/bin/env python3
"""
Helper script to retrieve Aurora Serverless credentials from AWS Secrets Manager
and update the .env file automatically
"""

import boto3
import json
import os
from dotenv import load_dotenv

def get_aurora_credentials():
    """Retrieve Aurora credentials from Secrets Manager"""
    
    # Load current environment
    load_dotenv()
    
    try:
        # Get CloudFormation stack outputs
        cf_client = boto3.client('cloudformation')
        response = cf_client.describe_stacks(StackName='LangGraphMem0AuroraStack')
        
        outputs = {}
        if response['Stacks']:
            stack_outputs = response['Stacks'][0].get('Outputs', [])
            for output in stack_outputs:
                outputs[output['OutputKey']] = output['OutputValue']
        
        # Get secret ARN from outputs
        secret_arn = outputs.get('DatabaseSecretArn')
        if not secret_arn:
            print("❌ Could not find DatabaseSecretArn in stack outputs")
            return None
        
        # Retrieve secret from Secrets Manager
        secrets_client = boto3.client('secretsmanager')
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(secret_response['SecretString'])
        
        # Combine with other outputs
        credentials = {
            'POSTGRES_HOST': outputs.get('AuroraClusterEndpoint'),
            'POSTGRES_PORT': outputs.get('AuroraClusterPort', '5432'),
            'POSTGRES_USER': secret_data.get('username'),
            'POSTGRES_PASSWORD': secret_data.get('password'),
            'POSTGRES_DB': outputs.get('DatabaseName', 'mem0_agent'),
            'POSTGRES_SSL_MODE': 'require',
            'POSTGRES_CONNECT_TIMEOUT': '30',
            'POSTGRES_APPLICATION_NAME': 'langgraph-mem0-agent'
        }
        
        return credentials
        
    except Exception as e:
        print(f"❌ Error retrieving Aurora credentials: {e}")
        return None

def update_env_file(credentials):
    """Update .env file with Aurora credentials"""
    
    if not credentials:
        return False
    
    try:
        # Read existing .env file
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        # Update or add credentials
        updated_keys = set()
        new_env_lines = []
        
        for line in env_lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0]
                if key in credentials:
                    new_env_lines.append(f"{key}={credentials[key]}\n")
                    updated_keys.add(key)
                else:
                    new_env_lines.append(line + '\n')
            else:
                new_env_lines.append(line + '\n')
        
        # Add missing credentials
        for key, value in credentials.items():
            if key not in updated_keys:
                new_env_lines.append(f"{key}={value}\n")
        
        # Write updated .env file
        with open('.env', 'w') as f:
            f.writelines(new_env_lines)
        
        print("✅ .env file updated with Aurora credentials")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main function"""
    print("🔐 Retrieving Aurora Serverless credentials...")
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Using AWS account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials not available: {e}")
        return
    
    # Get credentials
    credentials = get_aurora_credentials()
    if not credentials:
        print("❌ Failed to retrieve Aurora credentials")
        return
    
    # Display credentials (without password)
    print("\n📋 Aurora Connection Details:")
    for key, value in credentials.items():
        if 'PASSWORD' in key:
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")
    
    # Update .env file
    if update_env_file(credentials):
        print("\n🎉 Aurora credentials retrieved and .env file updated successfully!")
        print("\n📝 Next steps:")
        print("1. Test connection: python setup_postgres.py")
        print("2. Run the agent: python langgraph_mem0_agent.py")
    else:
        print("\n⚠️  Failed to update .env file")

if __name__ == "__main__":
    main()
