# CRITICAL: Disable telemetry BEFORE any other imports
import os
import sys
import uuid
import warnings

# Set all telemetry environment variables
os.environ["MEM0_TELEMETRY"] = "false"
os.environ["POSTHOG_DISABLED"] = "true"
os.environ["POSTHOG_PERSONAL_API_KEY"] = ""
os.environ["MEM0_USER_ID"] = str(uuid.uuid4())
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"

# Mock PostHog completely before it can be imported
class MockPostHogClient:
    def __init__(self, *args, **kwargs):
        pass
    def capture(self, *args, **kwargs):
        pass
    def identify(self, *args, **kwargs):
        pass
    def alias(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass
    def shutdown(self, *args, **kwargs):
        pass

class MockPosthog:
    """Mock the Posthog class that Mem0 tries to import"""
    def __init__(self, *args, **kwargs):
        pass
    def capture(self, *args, **kwargs):
        pass
    def identify(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass
    def shutdown(self, *args, **kwargs):
        pass

class MockPostHogModule:
    Client = MockPostHogClient
    Posthog = MockPosthog  # This is what Mem0 is trying to import
    
    def capture(self, *args, **kwargs):
        pass
    def identify(self, *args, **kwargs):
        pass

# Replace posthog in sys.modules before any imports
mock_module = MockPostHogModule()
sys.modules['posthog'] = mock_module
sys.modules['posthog.client'] = mock_module

# Suppress warnings
warnings.simplefilter("ignore", DeprecationWarning)

# Set up logging after telemetry is disabled
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set UTF-8 encoding for proper Chinese text handling
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
from typing import List, Dict, Any
import boto3

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Mock mem0 telemetry functions
def mock_capture_event(*args, **kwargs):
    pass

# Disable mem0 telemetry after import
try:
    import mem0.memory.telemetry
    mem0.memory.telemetry.capture_event = mock_capture_event
    logger.info("✅ Mem0 telemetry disabled")
except ImportError:
    pass

# Page configuration
st.set_page_config(
    page_title="🧠 Memory Dashboard", 
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_mem0():
    """Initialize Mem0 with the same configuration as your main agent"""
    logger.info("🔧 Starting Mem0 initialization...")
    
    try:
        # Import Memory after telemetry is disabled
        from mem0 import Memory
        
        # Verify AWS credentials are available (using boto3 default credential chain)
        logger.info("🔍 Checking AWS credentials...")
        try:
            # Test AWS credentials by creating a client
            test_client = boto3.client('sts', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))
            caller_identity = test_client.get_caller_identity()
            logger.info(f"✅ AWS credentials verified for account: {caller_identity.get('Account', 'unknown')}")
            st.sidebar.success("✅ AWS credentials verified")
        except Exception as e:
            logger.error(f"❌ AWS credentials not available: {e}")
            st.sidebar.error(f"❌ AWS credentials not available: {e}")
            st.sidebar.error("Please configure AWS credentials using 'aws configure' or environment variables")
            return None
        
        logger.info("🔧 Building Mem0 configuration...")
        config = {  
            "version": "v1.1",  
            "llm": {  
                "provider": "aws_bedrock",  
                "config": {  
                    "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Claude 3.7 Sonnet (cross-region)
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
                "provider": "pgvector",  
                "config": {  
                    "host": os.getenv('POSTGRES_HOST', 'localhost'),
                    "port": int(os.getenv('POSTGRES_PORT', '5432')),
                    "user": os.getenv('POSTGRES_USER', 'postgres'),
                    "password": os.getenv('POSTGRES_PASSWORD', ''),
                    "dbname": os.getenv('POSTGRES_DB', 'mem0_agent'),
                }  
            }  
        }
        
        logger.info(f"📊 Configuration details:")
        logger.info(f"  - LLM Model: {config['llm']['config']['model']}")
        logger.info(f"  - Embedder Model: {config['embedder']['config']['model']}")
        logger.info(f"  - AWS Region: {config['llm']['config']['aws_region']}")
        logger.info(f"  - DB Host: {config['vector_store']['config']['host']}")
        logger.info(f"  - DB Port: {config['vector_store']['config']['port']}")
        logger.info(f"  - DB Name: {config['vector_store']['config']['dbname']}")
        logger.info(f"  - DB User: {config['vector_store']['config']['user']}")
        
        # Debug information
        st.sidebar.write("🔧 **Debug Info:**")
        st.sidebar.write(f"Host: {config['vector_store']['config']['host']}")
        st.sidebar.write(f"Port: {config['vector_store']['config']['port']}")
        st.sidebar.write(f"Database: {config['vector_store']['config']['dbname']}")
        st.sidebar.write(f"User: {config['vector_store']['config']['user']}")
        st.sidebar.write(f"AWS Region: {config['llm']['config']['aws_region']}")
        
        logger.info("🚀 Creating Mem0 instance...")
        mem0_instance = Memory.from_config(config)
        logger.info("✅ Mem0 instance created successfully")
        
        st.sidebar.success("✅ Mem0 initialized successfully")
        return mem0_instance
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Mem0: {str(e)}", exc_info=True)
        st.sidebar.error(f"❌ Failed to initialize Mem0: {str(e)}")
        st.sidebar.write("**Possible solutions:**")
        st.sidebar.write("1. Check your .env file configuration")
        st.sidebar.write("2. Ensure PostgreSQL is running")
        st.sidebar.write("3. Verify AWS credentials")
        st.sidebar.write("4. Check if pgvector extension is installed")
        st.sidebar.write("5. Try running your main agent first")
        return None

def test_mem0_connection():
    """Test Mem0 connection and provide debugging info"""
    st.subheader("🔧 Connection Test")
    
    with st.expander("🔍 Test Mem0 Connection"):
        if st.button("Test Connection"):
            logger.info("🧪 Starting connection test...")
            
            mem0 = init_mem0()
            if mem0 is None:
                logger.error("❌ Cannot initialize Mem0 for testing")
                st.error("❌ Cannot initialize Mem0")
                return False
            
            try:
                # Show available methods
                st.write("**Available Mem0 methods:**")
                methods = [method for method in dir(mem0) if not method.startswith('_') and callable(getattr(mem0, method))]
                st.write(methods)
                logger.info(f"📋 Available methods: {methods}")
                
                # Test the search method (like your main agent uses)
                st.write("**Testing search method (like main agent):**")
                test_user_id = "default_user"
                
                # Test different search queries
                for test_query in ["user", "conversation", "hello", ""]:
                    logger.info(f"🧪 Testing search with query: '{test_query}'")
                    st.write(f"Testing search query: '{test_query}'")
                    
                    try:
                        logger.info(f"🔍 Calling mem0.search('{test_query}', user_id='{test_user_id}')")
                        search_result = mem0.search(test_query, user_id=test_user_id)
                        
                        logger.info(f"📊 Search result type: {type(search_result)}")
                        logger.info(f"📊 Search result content: {search_result}")
                        
                        st.success(f"✅ search('{test_query}', user_id='{test_user_id}') works!")
                        st.write(f"Result type: {type(search_result)}")
                        
                        if isinstance(search_result, dict):
                            st.write("Search result keys:", list(search_result.keys()))
                            if "results" in search_result:
                                results = search_result["results"]
                                st.write(f"Found {len(results)} memories in results")
                                logger.info(f"✅ Found {len(results)} memories in results")
                                
                                if results:
                                    st.write("**Sample memory:**")
                                    sample = results[0]
                                    logger.info(f"📋 Sample memory type: {type(sample)}")
                                    
                                    if isinstance(sample, dict):
                                        st.json(sample)
                                        logger.info(f"📋 Sample memory keys: {list(sample.keys())}")
                                    else:
                                        st.write(f"Memory object: {sample}")
                                        logger.info(f"📋 Sample memory: {sample}")
                                        if hasattr(sample, '__dict__'):
                                            logger.info(f"📋 Sample memory attributes: {list(sample.__dict__.keys())}")
                                break  # Found working query, stop testing
                        else:
                            st.write(f"Direct results: {len(search_result) if search_result else 0} memories")
                            logger.info(f"📊 Direct results: {len(search_result) if search_result else 0} memories")
                            if search_result:
                                break  # Found working query, stop testing
                            
                    except Exception as e:
                        logger.error(f"❌ search('{test_query}') failed: {str(e)}", exc_info=True)
                        st.error(f"❌ search('{test_query}') failed: {str(e)}")
                
                # Test get_all methods
                st.write("**Testing get_all methods:**")
                logger.info("🧪 Testing get_all methods...")
                
                for param_name in ['user_id', 'agent_id', 'run_id']:
                    logger.info(f"🧪 Testing get_all with {param_name}")
                    try:
                        logger.info(f"🔍 Calling mem0.get_all({param_name}='{test_user_id}')")
                        test_memories = mem0.get_all(**{param_name: test_user_id})
                        
                        logger.info(f"📊 get_all({param_name}) result type: {type(test_memories)}")
                        logger.info(f"📊 get_all({param_name}) result: {test_memories}")
                        
                        # Handle different return types from get_all()
                        if isinstance(test_memories, dict):
                            # If it's a dict, it might have a 'results' key or be structured differently
                            if 'results' in test_memories:
                                memories_list = test_memories['results']
                                st.success(f"✅ get_all({param_name}='{test_user_id}') works! Found {len(memories_list)} memories in results")
                            else:
                                # If it's a dict but no 'results' key, show the structure
                                st.success(f"✅ get_all({param_name}='{test_user_id}') works! Returned dict with keys: {list(test_memories.keys())}")
                                memories_list = []
                                
                                # Try to extract memories from common dict structures
                                for key, value in test_memories.items():
                                    if isinstance(value, list):
                                        memories_list.extend(value)
                                        
                        elif isinstance(test_memories, list):
                            memories_list = test_memories
                            st.success(f"✅ get_all({param_name}='{test_user_id}') works! Found {len(memories_list)} memories")
                        else:
                            st.warning(f"⚠️ get_all({param_name}='{test_user_id}') returned unexpected type: {type(test_memories)}")
                            memories_list = []
                        
                        # Show sample memory if available
                        if memories_list:
                            sample = memories_list[0]
                            st.write(f"Sample memory type: {type(sample)}")
                            logger.info(f"📋 Sample get_all memory type: {type(sample)}")
                            
                            if hasattr(sample, '__dict__'):
                                st.write("Sample memory attributes:", list(sample.__dict__.keys()))
                                logger.info(f"📋 Sample get_all memory attributes: {list(sample.__dict__.keys())}")
                            elif isinstance(sample, dict):
                                st.write("Sample memory keys:", list(sample.keys()))
                                logger.info(f"📋 Sample get_all memory keys: {list(sample.keys())}")
                                
                                # Show a preview of the memory content
                                if 'memory' in sample:
                                    st.write(f"Memory content preview: {str(sample['memory'])[:100]}...")
                                elif 'text' in sample:
                                    st.write(f"Memory text preview: {str(sample['text'])[:100]}...")
                        else:
                            st.info(f"ℹ️ No memories found for user '{test_user_id}'")
                    except Exception as e:
                        logger.error(f"❌ get_all({param_name}) failed: {str(e)}", exc_info=True)
                        st.error(f"❌ get_all({param_name}) failed: {str(e)}")
                
                logger.info("✅ Connection test completed")
                return True
                
            except Exception as e:
                logger.error(f"❌ Connection test failed: {str(e)}", exc_info=True)
                st.error(f"❌ Connection test failed: {str(e)}")
                return False

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_user_memories(user_id: str) -> List[Dict[Any, Any]]:
    """Get all memories for a specific user"""
    logger.info(f"🔍 Starting get_user_memories for user_id: '{user_id}'")
    
    try:
        mem0 = init_mem0()
        if mem0 is None:
            logger.error("❌ Mem0 initialization failed")
            return []
        
        # Ensure user_id is not None or empty
        if not user_id or user_id.strip() == "":
            logger.warning("⚠️ User ID is empty")
            st.warning("User ID cannot be empty")
            return []
        
        logger.info(f"📊 Attempting to fetch memories for user_id: '{user_id}'")
        
        # Method 1: Try using search with a non-empty query to get memories
        logger.info("🔍 Method 1: Trying search with 'user' query...")
        try:
            # Use a simple query that should match most conversations
            search_query = "user"
            logger.info(f"🔍 Calling mem0.search('{search_query}', user_id='{user_id}')")
            
            search_result = mem0.search(search_query, user_id=user_id)
            logger.info(f"📊 Search result type: {type(search_result)}")
            logger.info(f"📊 Search result: {search_result}")
            
            if isinstance(search_result, dict) and "results" in search_result:
                memories = search_result["results"]
                logger.info(f"✅ Found {len(memories)} memories in search results")
            else:
                memories = search_result
                logger.info(f"✅ Direct search results: {len(memories) if memories else 0} memories")
            
            if memories:
                logger.info("🔄 Processing memory objects...")
                processed_memories = []
                for i, memory in enumerate(memories):
                    logger.info(f"  Processing memory {i+1}: type={type(memory)}")
                    
                    if isinstance(memory, dict):
                        logger.info(f"    Memory {i+1} is dict with keys: {list(memory.keys())}")
                        processed_memories.append(memory)
                    elif hasattr(memory, '__dict__'):
                        logger.info(f"    Memory {i+1} is object with attributes: {list(memory.__dict__.keys())}")
                        processed_memories.append(memory.__dict__)
                    else:
                        logger.info(f"    Memory {i+1} is other type, creating basic structure")
                        # Create a basic memory structure
                        memory_dict = {
                            'id': getattr(memory, 'id', str(uuid.uuid4())),
                            'memory': str(memory),
                            'user_id': user_id,
                            'created_at': getattr(memory, 'created_at', datetime.now().isoformat()),
                            'updated_at': getattr(memory, 'updated_at', datetime.now().isoformat()),
                            'metadata': getattr(memory, 'metadata', {})
                        }
                        processed_memories.append(memory_dict)
                
                logger.info(f"✅ Successfully processed {len(processed_memories)} memories")
                return processed_memories
            else:
                logger.info("📭 No memories found in search results")
                
        except Exception as e1:
            logger.error(f"❌ Search method failed: {str(e1)}", exc_info=True)
            st.error(f"Search method failed: {str(e1)}")
            
            # Method 2: Try get_all with user_id
            logger.info("🔍 Method 2: Trying get_all with user_id...")
            try:
                logger.info(f"🔍 Calling mem0.get_all(user_id='{user_id}')")
                memories = mem0.get_all(user_id=user_id)
                logger.info(f"📊 get_all result type: {type(memories)}")
                logger.info(f"📊 get_all result: {memories}")
                
                # Handle different return types from get_all()
                memories_list = []
                if isinstance(memories, dict):
                    logger.info("📊 get_all returned a dictionary")
                    if 'results' in memories:
                        memories_list = memories['results']
                        logger.info(f"📊 Found {len(memories_list)} memories in 'results' key")
                    else:
                        # Try to extract memories from other possible keys
                        for key, value in memories.items():
                            if isinstance(value, list):
                                memories_list.extend(value)
                                logger.info(f"📊 Found {len(value)} memories in '{key}' key")
                        
                        if not memories_list:
                            logger.info("📊 No list values found in dictionary, treating as single memory")
                            # If the dict itself looks like a memory, treat it as one
                            if 'memory' in memories or 'text' in memories or 'id' in memories:
                                memories_list = [memories]
                elif isinstance(memories, list):
                    memories_list = memories
                    logger.info(f"📊 get_all returned a list with {len(memories_list)} items")
                else:
                    logger.warning(f"📊 get_all returned unexpected type: {type(memories)}")
                    memories_list = []
                
                if memories_list:
                    logger.info("🔄 Processing get_all memory objects...")
                    processed_memories = []
                    for i, memory in enumerate(memories_list):
                        logger.info(f"  Processing get_all memory {i+1}: type={type(memory)}")
                        
                        try:
                            if isinstance(memory, dict):
                                logger.info(f"    get_all Memory {i+1} is dict with keys: {list(memory.keys())}")
                                processed_memories.append(memory)
                            elif hasattr(memory, '__dict__'):
                                logger.info(f"    get_all Memory {i+1} is object with attributes: {list(memory.__dict__.keys())}")
                                processed_memories.append(memory.__dict__)
                            else:
                                logger.info(f"    get_all Memory {i+1} is other type: {type(memory)}")
                                logger.info(f"    get_all Memory {i+1} dir: {dir(memory)}")
                                memory_dict = {
                                    'id': getattr(memory, 'id', str(uuid.uuid4())),
                                    'memory': str(memory),
                                    'user_id': user_id,
                                    'created_at': getattr(memory, 'created_at', datetime.now().isoformat()),
                                    'updated_at': getattr(memory, 'updated_at', datetime.now().isoformat()),
                                    'metadata': getattr(memory, 'metadata', {})
                                }
                                processed_memories.append(memory_dict)
                        except Exception as mem_error:
                            logger.error(f"❌ Error processing memory {i+1}: {str(mem_error)}", exc_info=True)
                            continue
                    
                    logger.info(f"✅ Successfully processed {len(processed_memories)} memories from get_all")
                    return processed_memories
                else:
                    logger.info("📭 No memories found in get_all results")
                    
            except Exception as e2:
                logger.error(f"❌ get_all method failed: {str(e2)}", exc_info=True)
                st.error(f"get_all method failed: {str(e2)}")
                
                # Method 3: Try alternative search queries
                logger.info("🔍 Method 3: Trying alternative search queries...")
                try:
                    # Try searching with different queries that might match stored memories
                    for query in ["conversation", "assistant", "hello", "I"]:
                        logger.info(f"🔍 Trying search query: '{query}'")
                        try:
                            search_result = mem0.search(query, user_id=user_id)
                            logger.info(f"📊 Query '{query}' result: {type(search_result)}")
                            
                            if isinstance(search_result, dict) and "results" in search_result:
                                memories = search_result["results"]
                                if memories:
                                    logger.info(f"✅ Found memories using search query: '{query}' - {len(memories)} results")
                                    st.info(f"Found memories using search query: '{query}'")
                                    return memories
                            elif search_result:
                                logger.info(f"✅ Found memories using direct search query: '{query}' - {len(search_result)} results")
                                st.info(f"Found memories using search query: '{query}'")
                                return search_result
                        except Exception as query_error:
                            logger.warning(f"⚠️ Query '{query}' failed: {str(query_error)}")
                            continue
                    
                    logger.info("📭 No memories found with any search query")
                    return []
                    
                except Exception as e3:
                    logger.error(f"❌ Alternative search failed: {str(e3)}", exc_info=True)
                    st.error(f"Alternative search failed: {str(e3)}")
                    return []
        
        logger.info("📭 All methods completed, no memories found")
        return []
        
    except Exception as e:
        logger.error(f"❌ Error in get_user_memories: {str(e)}", exc_info=True)
        st.error(f"Error in get_user_memories: {str(e)}")
        return []

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return timestamp
    return str(timestamp)

def categorize_memory(memory_text: str) -> str:
    """Simple categorization based on keywords"""
    memory_lower = memory_text.lower()
    
    if any(word in memory_lower for word in ['like', 'love', 'enjoy', 'prefer', 'favorite']):
        return "🎯 Preferences"
    elif any(word in memory_lower for word in ['work', 'job', 'career', 'company', 'project']):
        return "💼 Professional"
    elif any(word in memory_lower for word in ['family', 'friend', 'relationship', 'partner']):
        return "👥 Personal"
    elif any(word in memory_lower for word in ['hobby', 'sport', 'music', 'movie', 'book']):
        return "🎨 Interests"
    elif any(word in memory_lower for word in ['travel', 'trip', 'vacation', 'visit']):
        return "✈️ Travel"
    else:
        return "📝 General"

def get_memory_type(memory: Dict[Any, Any]) -> str:
    """Extract memory type from memory data - show all types as they are"""
    # Check if memory type is in metadata
    if 'metadata' in memory and memory['metadata']:
        metadata = memory['metadata']
        if 'memory_type' in metadata:
            return str(metadata['memory_type']).upper()
        elif 'type' in metadata:
            return str(metadata['type']).upper()
    
    # Check if memory type is a direct field
    if 'memory_type' in memory:
        return str(memory['memory_type']).upper()
    elif 'type' in memory:
        return str(memory['type']).upper()
    
    # Default fallback
    return "UNKNOWN"

def show_logs():
    """Display recent logs"""
    st.subheader("📋 Recent Logs")
    
    with st.expander("🔍 View Dashboard Logs"):
        try:
            if os.path.exists('memory_dashboard.log'):
                with open('memory_dashboard.log', 'r') as f:
                    logs = f.readlines()
                
                # Show last 50 lines
                recent_logs = logs[-50:] if len(logs) > 50 else logs
                
                st.text_area(
                    "Recent log entries:",
                    value=''.join(recent_logs),
                    height=300,
                    help="Last 50 log entries from memory_dashboard.log"
                )
                
                if st.button("Clear Logs"):
                    with open('memory_dashboard.log', 'w') as f:
                        f.write("")
                    st.success("Logs cleared!")
                    st.rerun()
            else:
                st.info("No log file found yet. Logs will appear after running operations.")
                
        except Exception as e:
            st.error(f"Error reading logs: {str(e)}")

def main():
    # Header
    st.title("🧠 AI Agent Memory Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("🔧 Controls")
    user_id = st.sidebar.text_input("👤 User ID", value="default_user", help="Enter the user ID to view memories")
    
    if st.sidebar.button("🔄 Refresh Data"):
        logger.info("🔄 User requested data refresh")
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Dashboard Info")
    st.sidebar.info("This dashboard displays the current memory state for the specified user ID.")
    
    # Show logs section
    show_logs()
    
    # Connection test section
    test_mem0_connection()
    
    # Main content
    if not user_id.strip():
        st.warning("⚠️ Please enter a User ID to view memories.")
        logger.warning("⚠️ Empty user ID provided")
        return
    
    logger.info(f"🎯 Main dashboard starting for user_id: '{user_id}'")
    
    # Get memories
    with st.spinner(f"🔍 Loading memories for user: {user_id}..."):
        logger.info(f"🔍 Loading memories for user: {user_id}")
        memories = get_user_memories(user_id)
        logger.info(f"📊 Retrieved {len(memories)} memories")
    
    if not memories:
        st.warning(f"📭 No memories found for user: {user_id}")
        st.info("💡 Try interacting with the AI agent first to create some memories!")
        logger.info(f"📭 No memories found for user: {user_id}")
        return
    
    # Overview metrics
    st.subheader("📈 Memory Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🧠 Total Memories", len(memories))
    
    with col2:
        # Recent memories (last 24 hours)
        recent_count = 0
        now = datetime.now()
        for memory in memories:
            try:
                created_at = memory.get('created_at', '')
                if created_at:
                    memory_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if (now - memory_time.replace(tzinfo=None)) < timedelta(days=1):
                        recent_count += 1
            except:
                pass
        st.metric("🕐 Recent (24h)", recent_count)
    
    with col3:
        # Average memory length
        avg_length = sum(len(memory.get('memory', '')) for memory in memories) / len(memories)
        st.metric("📏 Avg Length", f"{avg_length:.0f} chars")
    
    st.markdown("---")
    
    # Detailed memory list
    st.subheader("📋 Detailed Memory List")
    
    # Calculate categories for filter dropdown
    category_data = {}
    for memory in memories:
        category = categorize_memory(memory.get('memory', ''))
        category_data[category] = category_data.get(category, 0) + 1
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search memories", placeholder="Enter keywords to search...")
    with col2:
        category_filter = st.selectbox("🏷️ Filter by category", ["All"] + list(category_data.keys()))
    
    # Filter memories
    filtered_memories = memories
    if search_term:
        filtered_memories = [m for m in filtered_memories 
                           if search_term.lower() in m.get('memory', '').lower()]
    
    if category_filter != "All":
        filtered_memories = [m for m in filtered_memories 
                           if categorize_memory(m.get('memory', '')) == category_filter]
    
    st.write(f"📊 Showing {len(filtered_memories)} of {len(memories)} memories")
    
    # Sort memories by created_at date (newest first)
    def get_memory_date(memory):
        created_at = memory.get('created_at', '')
        if created_at:
            try:
                return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return datetime.min
        return datetime.min
    
    sorted_memories = sorted(filtered_memories, key=get_memory_date, reverse=True)
    
    # Display memories
    for i, memory in enumerate(sorted_memories):
        memory_type = get_memory_type(memory)
        memory_date = format_timestamp(memory.get('created_at', 'N/A'))
        
        with st.expander(f"{memory_type} - {memory_date} - {memory.get('memory', '')[:50]}..."):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**💭 Memory Content:**")
                st.write(memory.get('memory', 'No content'))
                
                if 'metadata' in memory and memory['metadata']:
                    st.write("**📋 Metadata:**")
                    st.json(memory['metadata'])
            
            with col2:
                st.write("**📊 Details:**")
                st.write(f"**🏷️ Category:** {categorize_memory(memory.get('memory', ''))}")
                st.write(f"**🔧 Memory Type:** {memory_type}")
                st.write(f"**🆔 ID:** {memory.get('id', 'N/A')}")
                st.write(f"**👤 User ID:** {memory.get('user_id', 'N/A')}")
                st.write(f"**📅 Created:** {format_timestamp(memory.get('created_at', 'N/A'))}")
                st.write(f"**🔄 Updated:** {format_timestamp(memory.get('updated_at', 'N/A'))}")
                
                if 'score' in memory:
                    st.write(f"**⭐ Score:** {memory.get('score', 'N/A')}")
    
    # Raw data view (collapsible)
    with st.expander("🔍 Raw Memory Data (JSON)"):
        st.json(filtered_memories)

if __name__ == "__main__":
    main()
