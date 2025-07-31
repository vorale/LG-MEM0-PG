# Aurora Serverless v2 Deployment Guide

This guide walks you through deploying AWS Aurora Serverless v2 PostgreSQL with pgvector extension for your LangGraph + Mem0 Agent.

## 🏗️ Infrastructure Overview

The CDK stack creates:
- **Aurora Serverless v2 PostgreSQL cluster** with pgvector extension
- **VPC** with public/private subnets across 2 AZs
- **Security Groups** with PostgreSQL access
- **AWS Secrets Manager** for database credentials
- **CloudWatch Logs** for monitoring
- **Automatic scaling** from 0.5 to 16 ACUs

## 📋 Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Node.js** installed (for CDK CLI)
3. **Python 3.8+** with pip
4. **AWS account** with Aurora and Secrets Manager permissions

### Required AWS Permissions

Your AWS user/role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:*",
                "ec2:*",
                "secretsmanager:*",
                "cloudformation:*",
                "iam:*",
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🚀 Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Install dependencies and deploy everything
python deploy_infrastructure.py
```

This script will:
- Install CDK CLI and Python dependencies
- Bootstrap CDK in your AWS account
- Deploy the Aurora Serverless stack
- Enable pgvector extension
- Update your .env file with connection details

### Option 2: Manual Step-by-Step Deployment

```bash
# 1. Install CDK CLI (if not already installed)
npm install -g aws-cdk

# 2. Install Python dependencies
pip install -r requirements-cdk.txt

# 3. Bootstrap CDK (one-time per account/region)
cdk bootstrap

# 4. Deploy the stack
cdk deploy LangGraphMem0AuroraStack --require-approval never

# 5. Get Aurora credentials and update .env
python get_aurora_credentials.py

# 6. Enable pgvector extension (if not done automatically)
python setup_postgres.py
```

## 🔧 Configuration Options

### Scaling Configuration

Edit `infrastructure/aurora_stack.py` to adjust scaling:

```python
# Serverless v2 configuration
serverless_v2_min_capacity=0.5,  # Minimum ACUs (0.5-128)
serverless_v2_max_capacity=16,   # Maximum ACUs (1-128)
```

### Security Configuration

**⚠️ Important Security Note**: The default security group allows connections from `0.0.0.0/0`. For production, update this in `aurora_stack.py`:

```python
# Replace this line:
peer=ec2.Peer.ipv4("0.0.0.0/0"),

# With your specific IP:
peer=ec2.Peer.ipv4("YOUR_IP_ADDRESS/32"),
```

### Cost Optimization

For development/testing:
- Minimum capacity: 0.5 ACU (~$0.06/hour when active)
- Maximum capacity: 2-4 ACU for small workloads
- Enable deletion protection: `False` (for easy cleanup)

For production:
- Minimum capacity: 1-2 ACU
- Maximum capacity: 16+ ACU based on load
- Enable deletion protection: `True`
- Use read replicas for read scaling

## 📊 Monitoring and Costs

### Cost Estimation
- **Aurora Serverless v2**: ~$0.12 per ACU-hour
- **Storage**: $0.10 per GB-month
- **I/O**: $0.20 per million requests
- **Backup**: $0.021 per GB-month

### Monitoring
- CloudWatch metrics available for CPU, connections, I/O
- PostgreSQL logs exported to CloudWatch
- Set up alarms for scaling events

## 🧪 Testing the Deployment

### 1. Test Database Connection

```bash
python setup_postgres.py
```

Expected output:
```
🐘 Setting up PostgreSQL database with pgvector
==================================================
✅ Connected to Aurora Serverless PostgreSQL
✅ pgvector extension is available
✅ Database setup completed successfully
```

### 2. Test Memory Operations

```bash
python test_memory.py
```

### 3. Run the Agent

```bash
python langgraph_mem0_agent.py
```

## 🔍 Troubleshooting

### Common Issues

**1. CDK Bootstrap Failed**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Bootstrap with explicit account/region
cdk bootstrap aws://ACCOUNT-ID/REGION
```

**2. Connection Timeout**
```bash
# Check security group allows your IP
# Verify VPC and subnet configuration
# Ensure Aurora cluster is in "available" state
```

**3. pgvector Extension Not Found**
```bash
# Connect to database manually and run:
CREATE EXTENSION IF NOT EXISTS vector;

# Or use the setup script:
python setup_postgres.py
```

**4. High Costs**
```bash
# Check current scaling in AWS Console
# Reduce max_capacity in CDK stack
# Consider pausing development clusters
```

### Debug Commands

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name LangGraphMem0AuroraStack

# Get Aurora cluster status
aws rds describe-db-clusters --db-cluster-identifier langgraph-mem0-aurora

# Test connection with psql
psql -h YOUR_ENDPOINT -U postgres -d mem0_agent -p 5432
```

## 🧹 Cleanup

### Destroy Infrastructure

```bash
# Destroy the CDK stack
cdk destroy LangGraphMem0AuroraStack

# Confirm deletion when prompted
```

**Note**: This will permanently delete:
- Aurora cluster and all data
- VPC and networking components
- Secrets Manager secret
- CloudWatch logs (after retention period)

### Partial Cleanup (Keep Data)

To reduce costs while keeping data:
1. Modify `serverless_v2_min_capacity` to 0.5
2. Redeploy: `cdk deploy LangGraphMem0AuroraStack`
3. Aurora will scale down when not in use

## 📚 Additional Resources

- [Aurora Serverless v2 Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [AWS CDK Python Documentation](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html)
- [Mem0 Documentation](https://docs.mem0.ai/)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review AWS CloudFormation events in the console
3. Check Aurora cluster logs in CloudWatch
4. Verify your AWS permissions and quotas

---

**Happy deploying! 🚀**
