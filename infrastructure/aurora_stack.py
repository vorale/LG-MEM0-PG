"""
Aurora Serverless v2 PostgreSQL Stack with pgvector extension
Optimized for LangGraph + Mem0 Agent with vector storage capabilities
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
)
from constructs import Construct
import json


class AuroraServerlessStack(Stack):
    """CDK Stack for Aurora Serverless v2 PostgreSQL with pgvector"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Configuration
        self.db_name = "mem0_agent"
        self.db_username = "postgres"
        
        # Use default VPC instead of creating new one
        self.vpc = self._get_default_vpc()
        
        # Create security group for Aurora
        self.security_group = self._create_security_group()
        
        # Create database credentials secret
        self.db_secret = self._create_database_secret()
        
        # Create custom DB parameter group for pgvector
        self.parameter_group = self._create_parameter_group()
        
        # Create Aurora Serverless v2 cluster
        self.aurora_cluster = self._create_aurora_cluster()
        
        # Create outputs
        self._create_outputs()

    def _get_default_vpc(self) -> ec2.Vpc:
        """Get the default VPC for the account/region"""
        return ec2.Vpc.from_lookup(
            self, "DefaultVPC",
            is_default=True
        )

    def _create_security_group(self) -> ec2.SecurityGroup:
        """Create security group for Aurora cluster"""
        sg = ec2.SecurityGroup(
            self, "AuroraSecurityGroup",
            vpc=self.vpc,
            description="Security group for Aurora Serverless PostgreSQL",
            security_group_name="langgraph-mem0-aurora-sg"
        )
        
        # Allow PostgreSQL connections from within VPC
        sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL access from VPC"
        )
        
        # Allow connections from your development machine
        # Note: Using 0.0.0.0/0 for development - restrict this in production
        sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("0.0.0.0/0"),
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL access for development (restrict in production)"
        )
        
        return sg

    def _create_database_secret(self) -> secretsmanager.Secret:
        """Create secret for database credentials"""
        return secretsmanager.Secret(
            self, "AuroraSecret",
            secret_name="langgraph-mem0-aurora-credentials",
            description="Aurora Serverless PostgreSQL credentials for LangGraph Mem0 Agent",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": self.db_username}),
                generate_string_key="password",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                password_length=32
            )
        )

    def _create_parameter_group(self) -> rds.ParameterGroup:
        """Create DB parameter group with optimized settings"""
        return rds.ParameterGroup(
            self, "AuroraParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_4
            ),
            description="Parameter group for Aurora PostgreSQL with optimized settings",
            parameters={
                # Remove vector from shared_preload_libraries as it's not supported
                # pgvector will be installed as a regular extension
                "log_statement": "all",
                "log_min_duration_statement": "1000",  # Log slow queries (>1s)
                "max_connections": "100"
            }
        )

    def _create_aurora_cluster(self) -> rds.DatabaseCluster:
        """Create Aurora Serverless v2 PostgreSQL cluster"""
        
        # Create Aurora cluster
        cluster = rds.DatabaseCluster(
            self, "AuroraCluster",
            cluster_identifier="langgraph-mem0-aurora",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_4
            ),
            credentials=rds.Credentials.from_secret(self.db_secret),
            default_database_name=self.db_name,
            parameter_group=self.parameter_group,
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC  # Use public subnets from default VPC
            ),
            security_groups=[self.security_group],
            
            # Serverless v2 configuration
            serverless_v2_min_capacity=0.5,  # Minimum 0.5 ACU
            serverless_v2_max_capacity=16,   # Maximum 16 ACU (adjust as needed)
            
            # Writer instance (required for Serverless v2)
            writer=rds.ClusterInstance.serverless_v2("Writer"),
            
            # Optional: Add reader instance for read scaling
            readers=[
                rds.ClusterInstance.serverless_v2("Reader")
            ],
            
            # Backup and maintenance
            backup=rds.BackupProps(
                retention=Duration.days(7),
                preferred_window="03:00-04:00"
            ),
            preferred_maintenance_window="sun:04:00-sun:05:00",
            
            # Monitoring
            monitoring_interval=Duration.seconds(60),
            
            # Logging
            cloudwatch_logs_exports=["postgresql"],
            cloudwatch_logs_retention=logs.RetentionDays.ONE_WEEK,
            
            # Security
            storage_encrypted=True,
            
            # Deletion protection (disable for development)
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY  # ⚠️ Use RETAIN for production
        )
        
        # Add custom resource to enable pgvector extension
        self._create_pgvector_custom_resource(cluster)
        
        return cluster

    def _create_pgvector_custom_resource(self, cluster: rds.DatabaseCluster):
        """Create custom resource to enable pgvector extension"""
        
        # Lambda function code to enable pgvector
        lambda_code = '''
import json
import boto3
import psycopg2
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """Enable pgvector extension in Aurora PostgreSQL"""
    
    try:
        if event['RequestType'] == 'Delete':
            return send_response(event, context, 'SUCCESS', {})
        
        # Get database connection details from event
        cluster_endpoint = event['ResourceProperties']['ClusterEndpoint']
        secret_arn = event['ResourceProperties']['SecretArn']
        database_name = event['ResourceProperties']['DatabaseName']
        
        # Get credentials from Secrets Manager
        secrets_client = boto3.client('secretsmanager')
        secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(secret_response['SecretString'])
        
        # Connect to database
        conn = psycopg2.connect(
            host=cluster_endpoint,
            port=5432,
            database=database_name,
            user=secret_data['username'],
            password=secret_data['password'],
            sslmode='require'
        )
        
        with conn.cursor() as cursor:
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Verify extension is installed
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()
            
            if result:
                logger.info("pgvector extension enabled successfully")
            else:
                raise Exception("Failed to enable pgvector extension")
        
        conn.commit()
        conn.close()
        
        return send_response(event, context, 'SUCCESS', {
            'Message': 'pgvector extension enabled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return send_response(event, context, 'FAILED', {
            'Message': str(e)
        })

def send_response(event, context, status, data):
    """Send response to CloudFormation"""
    import urllib3
    
    response_body = {
        'Status': status,
        'Reason': f'See CloudWatch Log Stream: {context.log_stream_name}',
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': data
    }
    
    http = urllib3.PoolManager()
    response = http.request(
        'PUT',
        event['ResponseURL'],
        body=json.dumps(response_body).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    return response_body
'''
        
        # Note: In a real implementation, you would create a Lambda function
        # and custom resource here. For now, we'll add instructions in outputs.
        pass

    def _create_outputs(self):
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self, "AuroraClusterEndpoint",
            value=self.aurora_cluster.cluster_endpoint.hostname,
            description="Aurora Serverless cluster endpoint",
            export_name="LangGraphMem0-AuroraEndpoint"
        )
        
        CfnOutput(
            self, "AuroraClusterPort",
            value=str(self.aurora_cluster.cluster_endpoint.port),
            description="Aurora Serverless cluster port",
            export_name="LangGraphMem0-AuroraPort"
        )
        
        CfnOutput(
            self, "DatabaseName",
            value=self.db_name,
            description="Database name",
            export_name="LangGraphMem0-DatabaseName"
        )
        
        CfnOutput(
            self, "DatabaseSecretArn",
            value=self.db_secret.secret_arn,
            description="ARN of the database credentials secret",
            export_name="LangGraphMem0-DatabaseSecretArn"
        )
        
        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="Default VPC ID used for Aurora cluster",
            export_name="LangGraphMem0-VpcId"
        )
        
        CfnOutput(
            self, "SecurityGroupId",
            value=self.security_group.security_group_id,
            description="Security Group ID for Aurora cluster",
            export_name="LangGraphMem0-SecurityGroupId"
        )
        
        # Instructions for manual pgvector setup
        CfnOutput(
            self, "PgvectorSetupInstructions",
            value="Connect to database and run: CREATE EXTENSION IF NOT EXISTS vector;",
            description="Manual command to enable pgvector extension"
        )
