#!/usr/bin/env python3
"""
OpenAI-Compatible FastAPI Service for LangGraph + Mem0 Agent

This service provides OpenAI-compatible endpoints for the enhanced LangGraph + Mem0 agent,
allowing integration with any OpenAI-compatible client.

Features:
- OpenAI-compatible chat completions endpoint
- Streaming and non-streaming responses
- User-specific memory management
- Memory statistics and maintenance endpoints
- Health check and service info endpoints
"""

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

# Now safe to import everything else
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from datetime import datetime

# Set UTF-8 encoding for proper Chinese text handling
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

# Set environment variable to suppress Python warnings
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"

# Suppress all deprecation warnings globally
warnings.simplefilter("ignore", DeprecationWarning)

# Set a unique user ID for telemetry to avoid the None error
os.environ["MEM0_USER_ID"] = str(uuid.uuid4())

# Disable telemetry completely
os.environ["MEM0_TELEMETRY"] = "false"
os.environ["POSTHOG_DISABLED"] = "true"
os.environ["POSTHOG_PERSONAL_API_KEY"] = ""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import logging

# Import the agent components
from mem0 import Memory  
from langgraph.graph import StateGraph, START, END  
from langgraph.graph.message import add_messages  
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage  
from langchain_community.tools.tavily_search import TavilySearchResults  
from langgraph.prebuilt import ToolNode  
import boto3
from dotenv import load_dotenv

# Import emotional companion prompts
from src.core.emotional_prompts import get_emotional_prompt

# Import our enhanced memory manager
from src.core.memory_manager import Mem0MemoryManager, MemoryType

# Configuration for emotional companion style
EMOTIONAL_COMPANION_STYLE = os.getenv('EMOTIONAL_COMPANION_STYLE', 'warm_friend')
# Available styles: warm_friend, gentle_healing, cheerful_companion, wise_mentor, caring_sibling

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="LangGraph + Mem0 Agent API",
    description="OpenAI-compatible API for LangGraph + Mem0 intelligent agent with memory",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for agent components
mem0_instance = None
memory_manager = None
agent_app = None
llm = None

# OpenAI-compatible request/response models
class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message author")
    content: str = Field(..., description="The content of the message")
    name: Optional[str] = Field(None, description="The name of the author")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="langgraph-mem0-agent", description="Model identifier")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: Optional[int] = Field(1000, ge=1, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    user: Optional[str] = Field("default_user", description="User identifier for memory management")
    top_p: Optional[float] = Field(0.9, ge=0, le=1, description="Nucleus sampling parameter")

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]

class ChatCompletionStreamChoice(BaseModel):
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]

# Memory management models
class MemoryStatsResponse(BaseModel):
    user_id: str
    total_memories: int
    by_type: Dict[str, int]
    average_importance: float
    memory_health: Dict[str, Any]

class MemoryMaintenanceResponse(BaseModel):
    user_id: str
    processed: int
    promoted: int
    demoted: int
    cleaned: int
    status: str

# Service info models
class ServiceInfo(BaseModel):
    name: str = "LangGraph + Mem0 Agent API"
    version: str = "1.0.0"
    description: str = "OpenAI-compatible API for intelligent agent with memory"
    features: List[str] = [
        "Long-term memory with Mem0 + PostgreSQL",
        "AWS Bedrock LLM (Claude-3.7-Sonnet)",
        "Web search with Tavily",
        "User-specific memory contexts",
        "Automatic memory promotion and maintenance",
        "Memory management endpoints matching original agent"
    ]
    endpoints: Dict[str, str] = {
        "chat_completions": "/v1/chat/completions",
        "memory_stats": "/v1/memory/stats/{user_id}",
        "memory_maintenance": "/v1/memory/maintenance/{user_id}",
        "memory_list": "/v1/memory/memories/{user_id}",
        "memory_clear": "/v1/memory/clear/{user_id}",
        "health": "/health",
        "info": "/info"
    }
    memory_commands: Dict[str, str] = {
        "stats": "GET /v1/memory/stats/{user_id} - Show memory statistics (matches /stats command)",
        "maintenance": "POST /v1/memory/maintenance/{user_id} - Run memory maintenance (matches /maintenance command)", 
        "memories": "GET /v1/memory/memories/{user_id}?memory_type=all&limit=10 - List memories (matches /memories command)",
        "clear": "DELETE /v1/memory/clear/{user_id}?memory_type=all - Clear memories (use with caution)"
    }

# State management for conversations
class ConversationState:
    def __init__(self):
        self.conversations: Dict[str, List[ChatMessage]] = {}
        self.user_conversations: Dict[str, List[str]] = {}
    
    def get_conversation_history(self, user_id: str, conversation_id: Optional[str] = None) -> List[ChatMessage]:
        """Get conversation history for a user"""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        # Return recent messages for the user
        user_convs = self.user_conversations.get(user_id, [])
        if user_convs:
            latest_conv = user_convs[-1]
            return self.conversations.get(latest_conv, [])
        
        return []
    
    def add_message(self, user_id: str, message: ChatMessage, conversation_id: Optional[str] = None):
        """Add a message to conversation history"""
        if not conversation_id:
            conversation_id = f"{user_id}_{int(time.time())}"
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            if user_id not in self.user_conversations:
                self.user_conversations[user_id] = []
            self.user_conversations[user_id].append(conversation_id)
        
        self.conversations[conversation_id].append(message)
        
        # Keep only last 50 messages per conversation to prevent memory bloat
        if len(self.conversations[conversation_id]) > 50:
            self.conversations[conversation_id] = self.conversations[conversation_id][-50:]

# Global conversation state
conversation_state = ConversationState()

def safe_decode(text):
    """安全解码文本，处理各种编码问题"""
    if text is None:
        return ""
    
    if isinstance(text, bytes):
        # Try multiple encoding strategies
        for enc in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
            try:
                return text.decode(enc)
            except UnicodeDecodeError:
                continue
        # Last resort: decode with errors='replace'
        return text.decode('utf-8', errors='replace')
    
    # Convert other types to string
    return str(text)

async def initialize_agent():
    """Initialize the agent components"""
    global mem0_instance, memory_manager, agent_app, llm
    
    if agent_app is not None:
        return  # Already initialized
    
    logger.info("🚀 Initializing LangGraph + Mem0 Agent...")
    
    # Verify AWS credentials
    try:
        test_client = boto3.client('sts', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))
        test_client.get_caller_identity()
        logger.info("✅ AWS credentials found")
    except Exception as e:
        logger.error(f"❌ AWS credentials not available: {e}")
        raise HTTPException(status_code=500, detail="AWS credentials not configured")

    # Check for Tavily API key (optional)
    tavily_enabled = bool(os.getenv('TAVILY_API_KEY') and os.getenv('TAVILY_API_KEY') != 'your-tavily-api-key')
    if not tavily_enabled:
        logger.warning("⚠️  Tavily API key not configured - web search will be disabled")

    # Initialize AWS Bedrock client
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    )

    # Initialize Mem0 with PostgreSQL
    mem0_instance = Memory.from_config({  
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
            "provider": "pgvector",  
            "config": {  
                "host": os.getenv('POSTGRES_HOST', 'localhost'),
                "port": int(os.getenv('POSTGRES_PORT', '5432')),
                "user": os.getenv('POSTGRES_USER', 'postgres'),
                "password": os.getenv('POSTGRES_PASSWORD', ''),
                "dbname": os.getenv('POSTGRES_DB', 'mem0_agent'),
            }  
        }  
    })

    # Initialize the enhanced memory manager
    logger.info("🧠 Initializing enhanced memory manager...")
    memory_manager = Mem0MemoryManager(mem0_instance, config={
        "enable_llm_classification": True,
        "enable_automatic_promotion": True,
        "maintenance_interval_hours": 6
    })
    logger.info("✅ Enhanced memory manager initialized")

    # Initialize LLM
    llm = ChatBedrock(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        client=bedrock_client,
        model_kwargs={
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9
        }
    )

    # Initialize tools if Tavily is enabled
    if tavily_enabled:
        tools = [TavilySearchResults(max_results=1)]  
        tool_node = ToolNode(tools)
        llm = llm.bind_tools(tools)
    else:
        tools = []
        tool_node = None

    # Build the LangGraph workflow
    from typing import Annotated, TypedDict
    
    class State(TypedDict):  
        messages: Annotated[List[HumanMessage | AIMessage], add_messages]
        mem0_user_id: str
        conversation_id: str
        session_memories: Dict[str, Any]

    def chatbot(state: State):
        """Enhanced chatbot with proper context management"""
        messages = state["messages"]  
        user_id = state["mem0_user_id"]
        conversation_id = state.get("conversation_id", str(uuid.uuid4()))

        logger.info(f"🤖 Processing message for user: {user_id}")

        # Get current user message
        current_user_message = safe_decode(messages[-1].content)
        
        # Get relevant long-term memories from Mem0
        try:
            logger.info("🔍 Searching relevant long-term memories...")
            search_results = mem0_instance.search(current_user_message, user_id=user_id)
            
            if isinstance(search_results, dict) and "results" in search_results:
                raw_memories = search_results["results"]
            else:
                raw_memories = search_results if search_results else []
            
            # Process memories safely
            relevant_memories = []
            for memory in raw_memories[:5]:  # Limit to 5 most relevant
                try:
                    if isinstance(memory, dict):
                        memory_content = memory.get('memory', '')
                        memory_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                        
                        if memory_type in ['core', 'long_term', 'short_term']:
                            relevant_memories.append({
                                'memory': memory_content,
                                'metadata': memory.get('metadata', {}),
                                'id': memory.get('id', 'unknown')
                            })
                except Exception as e:
                    logger.warning(f"Error processing memory: {e}")
                    continue
            
            # Build context from different memory types
            context_parts = []
            
            # Core memories
            core_memories = [m for m in relevant_memories 
                            if m.get('metadata', {}).get('memory_type') == 'core']
            if core_memories:
                context_parts.append("用户核心信息：")
                for memory in core_memories[:2]:
                    memory_text = safe_decode(memory.get('memory', ''))
                    context_parts.append(f"- {memory_text}")
            
            # Long-term memories
            long_term_memories = [m for m in relevant_memories 
                                 if m.get('metadata', {}).get('memory_type') == 'long_term']
            if long_term_memories:
                context_parts.append("用户偏好和重要信息：")
                for memory in long_term_memories[:3]:
                    memory_text = safe_decode(memory.get('memory', ''))
                    context_parts.append(f"- {memory_text}")
            
            # Short-term memories
            short_term_memories = [m for m in relevant_memories 
                                  if m.get('metadata', {}).get('memory_type') == 'short_term']
            if short_term_memories:
                context_parts.append("最近的重要信息：")
                for memory in short_term_memories[:2]:
                    memory_text = safe_decode(memory.get('memory', ''))
                    context_parts.append(f"- {memory_text}")
            
            if context_parts:
                long_term_context = "历史记忆中的相关信息：\n" + "\n".join(context_parts) + "\n"
            else:
                long_term_context = ""
                
            logger.info(f"📚 Retrieved {len(relevant_memories)} relevant long-term memories")
                
        except Exception as e:
            logger.warning(f"⚠️  Memory search failed: {e}")
            long_term_context = ""
        
        # Build system message with emotional companion prompt
        base_prompt = get_emotional_prompt(EMOTIONAL_COMPANION_STYLE)
        
        system_content_parts = [base_prompt]
        
        # Add long-term memory context
        if long_term_context:
            system_content_parts.append("\n📚 **用户记忆信息**：")
            system_content_parts.append(long_term_context)
        
        # Add conversation context awareness
        conversation_history = []
        for msg in messages[:-1]:  # Exclude current message
            if isinstance(msg, HumanMessage):
                conversation_history.append(f"User: {safe_decode(msg.content)}")
            elif isinstance(msg, AIMessage):
                conversation_history.append(f"Assistant: {safe_decode(msg.content)}")
        
        if len(conversation_history) > 0:
            system_content_parts.append("\n💭 **对话上下文**：你可以看到完整的对话历史，请根据上下文和用户的情感状态进行温暖的回复。")
        else:
            system_content_parts.append("\n🌟 **新对话开始**：这是与用户的新对话开始，请以温暖友善的方式打招呼。")
        
        system_content_parts.append("\n💝 **重要提醒**：请始终保持情感陪伴的特质，根据用户的历史信息、当前情绪和对话上下文，提供个性化的温暖陪伴。")
        
        system_content = "\n".join(system_content_parts)
        system_message = SystemMessage(content=safe_decode(system_content))

        # Generate response
        try:
            response = llm.invoke([system_message] + messages)
            response_content = safe_decode(response.content)
            response.content = response_content
            logger.info(f"🤖 Generated response: {response_content[:100]}...")
        except Exception as e:
            logger.error(f"❌ LLM invoke error: {e}")
            response = AIMessage(content="抱歉，处理您的请求时出现了错误。请稍后再试。")

        # Save to memory
        try:
            conversation_text = f"User: {current_user_message}\nAssistant: {response.content}"
            
            if memory_manager:
                memory_result = memory_manager.add_memory_with_type(
                    conversation_text, 
                    user_id,
                    context={
                        "conversation_id": conversation_id,
                        "type": "conversation_exchange",
                        "user_message": current_user_message,
                        "assistant_response": response.content
                    }
                )
                
                if memory_result.get("success"):
                    logger.info(f"✅ Memory saved with type: {memory_result.get('memory_type')}")
            else:
                # Fallback to simple memory saving
                mem0_instance.add(safe_decode(conversation_text), user_id=user_id)
                logger.info(f"✅ Fallback memory saved for user: {user_id}")
                
        except Exception as e:
            logger.warning(f"⚠️  Memory save failed: {e}")
        
        return {"messages": [response], "conversation_id": conversation_id}

    def should_continue(state):
        """Determine if tools should be called"""
        if not tavily_enabled:
            return "end"
        
        messages = state["messages"]  
        last_message = messages[-1]  
        
        if not last_message.tool_calls:  
            return "end"  
        else:  
            return "continue"

    # Build workflow
    workflow = StateGraph(State)
    workflow.add_node("agent", chatbot)
    
    if tavily_enabled and tool_node:
        workflow.add_node("action", tool_node)
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {"continue": "action", "end": END}
        )
        workflow.add_edge("action", "agent")
    else:
        workflow.add_edge("agent", END)
    
    workflow.add_edge(START, "agent")
    
    # Compile workflow
    agent_app = workflow.compile()
    
    logger.info("✅ Agent initialization complete")

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    await initialize_agent()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Service info endpoint
@app.get("/info", response_model=ServiceInfo)
async def service_info():
    """Get service information"""
    return ServiceInfo()

# Include memory management endpoints
try:
    from src.api.memory_endpoints import memory_router
    app.include_router(memory_router)
    logger.info("✅ Memory management endpoints loaded")
except ImportError as e:
    logger.warning(f"⚠️  Memory endpoints not available: {e}")

# Main chat completions endpoint (OpenAI compatible)
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    await initialize_agent()  # Ensure agent is initialized
    
    if request.stream:
        return StreamingResponse(
            stream_chat_completion(request),
            media_type="text/plain"
        )
    else:
        return await non_stream_chat_completion(request)

async def process_chat_command(user_message: str, user_id: str) -> tuple[bool, str]:
    """
    Process in-chat commands like /memories, /stats, /maintenance
    Returns (is_command, response_text)
    """
    if not user_message.startswith('/'):
        return False, ""
    
    # Parse command and arguments
    command_parts = user_message[1:].split()
    if not command_parts:
        return False, ""
    
    command = command_parts[0].lower()
    
    try:
        if command == 'stats':
            # Get memory statistics (matches /stats command from original agent)
            search_results = mem0_instance.search("user", user_id=user_id)
            
            if isinstance(search_results, dict) and "results" in search_results:
                memories = search_results["results"]
            else:
                memories = search_results if search_results else []
            
            if not memories:
                return True, f"📊 Memory Statistics for {user_id}:\n  No memories found for this user."
            
            # Calculate statistics (same logic as original agent)
            total_memories = len(memories)
            type_counts = {}
            total_importance = 0
            importance_count = 0
            
            for memory in memories:
                try:
                    if isinstance(memory, dict):
                        mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                        type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                        
                        importance = memory.get('metadata', {}).get('importance_level', 0)
                        if importance > 0:
                            total_importance += importance
                            importance_count += 1
                except Exception:
                    continue
            
            avg_importance = total_importance / importance_count if importance_count > 0 else 0.0
            
            response = f"📊 Memory Statistics for {user_id}:\n"
            response += f"  Total memories: {total_memories}\n"
            response += f"  By type: {type_counts}\n"
            response += f"  Average importance: {avg_importance:.2f}\n"
            response += f"  Memory health: {importance_count}/{total_memories} memories have importance scores"
            
            return True, response
            
        elif command == 'maintenance':
            # Run memory maintenance (matches /maintenance command from original agent)
            search_results = mem0_instance.search("user", user_id=user_id)
            
            if isinstance(search_results, dict) and "results" in search_results:
                memories = search_results["results"]
            else:
                memories = search_results if search_results else []
            
            memory_count = len(memories)
            
            if memory_count == 0:
                return True, f"🔧 Memory Maintenance for {user_id}:\n  ℹ️  No memories found for {user_id}"
            
            # Show memory type distribution (same as original agent)
            type_counts = {}
            for memory in memories:
                if isinstance(memory, dict):
                    mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                    type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
            
            response = f"🔧 Memory Maintenance for {user_id}:\n"
            response += f"  📊 Found {memory_count} memories\n"
            response += f"  ✅ Memory storage is functioning normally\n"
            response += f"  📈 Memory distribution: {type_counts}\n"
            
            # Try enhanced maintenance if available
            if memory_manager:
                try:
                    stats = memory_manager.run_memory_maintenance(user_id)
                    if stats.get("processed", 0) > 0:
                        response += f"  🔧 Advanced maintenance completed: {stats}"
                except Exception:
                    pass
            
            return True, response
            
        elif command == 'memories':
            # List memories (matches /memories command from original agent)
            memory_type = command_parts[1] if len(command_parts) > 1 else "all"
            
            # Get memories using search (same logic as original agent)
            if memory_type == "all":
                search_results = mem0_instance.search("user", user_id=user_id)
            else:
                search_results = mem0_instance.search(memory_type, user_id=user_id)
            
            if isinstance(search_results, dict) and "results" in search_results:
                memories = search_results["results"]
            else:
                memories = search_results if search_results else []
            
            if not memories:
                return True, f"📚 {memory_type.title()} memories for {user_id}:\n  No memories found."
            
            # Filter by type if specified (same logic as original agent)
            filtered_memories = []
            for memory in memories:
                try:
                    if isinstance(memory, dict):
                        mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                        
                        if (memory_type == "all" or 
                            memory_type == mem_type or 
                            (memory_type == "core" and mem_type == "core") or
                            (memory_type == "long" and mem_type == "long_term") or
                            (memory_type == "short" and mem_type == "short_term") or
                            (memory_type == "working" and mem_type == "working")):
                            
                            filtered_memories.append({
                                'memory': memory.get('memory', ''),
                                'metadata': memory.get('metadata', {}),
                                'id': memory.get('id', 'unknown')
                            })
                except Exception:
                    continue
            
            # Display memories (same format as original agent)
            response = f"📚 {memory_type.title()} memories for {user_id}:\n"
            
            for i, memory in enumerate(filtered_memories[:10], 1):  # Show top 10
                mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                importance = memory.get('metadata', {}).get('importance_level', 0)
                content = memory.get('memory', '')[:80]
                response += f"  {i}. [{mem_type}] (importance: {importance:.1f}) {content}...\n"
            
            if len(filtered_memories) > 10:
                response += f"  ... and {len(filtered_memories) - 10} more memories"
            
            return True, response
            
        elif command == 'help':
            # Show available commands
            response = "🔧 Available commands:\n"
            response += "  /stats - Show memory statistics\n"
            response += "  /maintenance - Run memory maintenance\n"
            response += "  /memories [type] - Show memories (type: core/long/short/working/all)\n"
            response += "  /help - Show this help\n"
            response += "\nExample: /memories core"
            
            return True, response
            
        else:
            return True, f"❌ Unknown command: /{command}\nType /help for available commands."
            
    except Exception as e:
        logger.error(f"Error processing command /{command}: {e}")
        return True, f"❌ Error processing command /{command}: {str(e)}"

async def non_stream_chat_completion(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """Handle non-streaming chat completion"""
    try:
        # Get the user message
        user_message = ""
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content
                break
        
        user_id = request.user or "default_user"
        
        # Check if this is a command
        is_command, command_response = await process_chat_command(user_message, user_id)
        
        if is_command:
            # Return command response directly
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
            
            return ChatCompletionResponse(
                id=completion_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=command_response),
                        finish_reason="stop"
                    )
                ],
                usage={
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(command_response.split()),
                    "total_tokens": len(user_message.split()) + len(command_response.split())
                }
            )
        
        # Convert OpenAI messages to LangChain messages
        langgraph_messages = []
        for msg in request.messages:
            if msg.role == "user":
                langgraph_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langgraph_messages.append(AIMessage(content=msg.content))
            # Skip system messages as they're handled internally
        
        # Create state for LangGraph
        user_id = request.user or "default_user"
        conversation_id = str(uuid.uuid4())
        
        initial_state = {
            "messages": langgraph_messages,
            "mem0_user_id": user_id,
            "conversation_id": conversation_id,
            "session_memories": {}
        }
        
        # Run the agent
        result = agent_app.invoke(initial_state)
        
        # Get the final response
        final_message = result["messages"][-1]
        response_content = final_message.content
        
        # Store conversation history
        for msg in request.messages:
            conversation_state.add_message(user_id, msg, conversation_id)
        
        conversation_state.add_message(
            user_id, 
            ChatMessage(role="assistant", content=response_content),
            conversation_id
        )
        
        # Create OpenAI-compatible response
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        
        return ChatCompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_content),
                    finish_reason="stop"
                )
            ],
            usage={
                "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
                "completion_tokens": len(response_content.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + len(response_content.split())
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_chat_completion(request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    """Handle streaming chat completion"""
    try:
        # Get the user message
        user_message = ""
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content
                break
        
        user_id = request.user or "default_user"
        
        # Check if this is a command
        is_command, command_response = await process_chat_command(user_message, user_id)
        
        if is_command:
            # Stream command response
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
            created = int(time.time())
            
            # Split response into chunks for streaming
            words = command_response.split()
            chunk_size = max(1, len(words) // 10)  # Split into ~10 chunks
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = " ".join(chunk_words)
                
                if i == 0:
                    # First chunk
                    delta = {"role": "assistant", "content": chunk_content}
                else:
                    # Subsequent chunks
                    delta = {"content": " " + chunk_content}
                
                chunk_response = ChatCompletionStreamResponse(
                    id=completion_id,
                    created=created,
                    model=request.model,
                    choices=[
                        ChatCompletionStreamChoice(
                            index=0,
                            delta=delta,
                            finish_reason=None
                        )
                    ]
                )
                
                yield f"data: {chunk_response.json()}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Final chunk
            final_chunk = ChatCompletionStreamResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta={},
                        finish_reason="stop"
                    )
                ]
            )
            
            yield f"data: {final_chunk.json()}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # For simplicity, we'll simulate streaming by yielding the complete response
        # In a real implementation, you'd want to stream tokens as they're generated
        
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        created = int(time.time())
        
        # Get non-streaming response first
        non_stream_request = ChatCompletionRequest(**request.dict())
        non_stream_request.stream = False
        
        response = await non_stream_chat_completion(non_stream_request)
        content = response.choices[0].message.content
        
        # Simulate streaming by splitting content into chunks
        words = content.split()
        chunk_size = max(1, len(words) // 10)  # Split into ~10 chunks
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = " ".join(chunk_words)
            
            if i == 0:
                # First chunk
                delta = {"role": "assistant", "content": chunk_content}
            else:
                # Subsequent chunks
                delta = {"content": chunk_content}
            
            chunk_response = ChatCompletionStreamResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[
                    ChatCompletionStreamChoice(
                        index=0,
                        delta=delta,
                        finish_reason=None
                    )
                ]
            )
            
            yield f"data: {chunk_response.json()}\n\n"
            await asyncio.sleep(0.1)  # Small delay to simulate streaming
        
        # Final chunk with finish_reason
        final_chunk = ChatCompletionStreamResponse(
            id=completion_id,
            created=created,
            model=request.model,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta={},
                    finish_reason="stop"
                )
            ]
        )
        
        yield f"data: {final_chunk.json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming chat completion: {e}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LangGraph + Mem0 Agent API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print("🚀 Starting LangGraph + Mem0 Agent API Server...")
    print(f"📡 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔗 OpenAI-compatible endpoint: http://{args.host}:{args.port}/v1/chat/completions")
    
    uvicorn.run(
        "openai_compatible_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
