#!/usr/bin/env python3
"""
AWS CDK App for LangGraph + Mem0 Agent Infrastructure
Provisions Aurora Serverless v2 PostgreSQL with pgvector extension
"""

import os
import aws_cdk as cdk
from infrastructure.aurora_stack import AuroraServerlessStack

app = cdk.App()

# Get environment configuration
env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region='us-west-2'  # Explicitly set to us-west-2
)

# Create Aurora Serverless stack
aurora_stack = AuroraServerlessStack(
    app, 
    "LangGraphMem0AuroraStack",
    env=env,
    description="Aurora Serverless v2 PostgreSQL with pgvector for LangGraph + Mem0 Agent"
)

# Add tags to all resources
cdk.Tags.of(app).add("Project", "LangGraph-Mem0-Agent")
cdk.Tags.of(app).add("Environment", "Development")
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
