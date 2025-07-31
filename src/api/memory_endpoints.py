"""
Memory Management Endpoints for OpenAI-Compatible Service

This module provides additional endpoints for memory management,
statistics, and maintenance operations that match the functionality
from the original langgraph_mem0_agent.py
"""

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Import will be handled at runtime to avoid circular imports
mem0_instance = None
memory_manager = None

def get_mem0_instance():
    """Get the mem0 instance from the main service"""
    global mem0_instance
    if mem0_instance is None:
        # Import here to avoid circular imports
        from src.api.service import mem0_instance as main_mem0
        mem0_instance = main_mem0
    return mem0_instance

def get_memory_manager():
    """Get the memory manager from the main service"""
    global memory_manager
    if memory_manager is None:
        # Import here to avoid circular imports
        from src.api.service import memory_manager as main_manager
        memory_manager = main_manager
    return memory_manager

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

# Define response models here to avoid circular imports
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
    memory_distribution: Dict[str, int]

class MemoryItem(BaseModel):
    id: str
    content: str
    type: str
    importance: float
    metadata: Dict[str, Any]

class MemoriesListResponse(BaseModel):
    user_id: str
    memory_type_filter: str
    total_found: int
    showing: int
    memories: List[MemoryItem]

# Create router for memory endpoints
memory_router = APIRouter(prefix="/v1/memory", tags=["memory"])

@memory_router.get("/stats/{user_id}", response_model=MemoryStatsResponse)
async def get_memory_stats(
    user_id: str = Path(..., description="User ID to get memory statistics for")
):
    """Get memory statistics for a specific user (matches /stats command from original agent)"""
    try:
        mem0_instance = get_mem0_instance()
        if not mem0_instance:
            raise HTTPException(status_code=500, detail="Memory system not initialized")
        
        # Get memories using direct mem0 search (same as original agent)
        search_results = mem0_instance.search("user", user_id=user_id)
        
        if isinstance(search_results, dict) and "results" in search_results:
            memories = search_results["results"]
        else:
            memories = search_results if search_results else []
        
        if not memories:
            return MemoryStatsResponse(
                user_id=user_id,
                total_memories=0,
                by_type={},
                average_importance=0.0,
                memory_health={"status": "no_memories"}
            )
        
        # Calculate statistics (same logic as original agent)
        total_memories = len(memories)
        type_counts = {}
        total_importance = 0
        importance_count = 0
        highly_accessed = 0
        
        for memory in memories:
            try:
                if isinstance(memory, dict):
                    # Count by type
                    mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                    type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                    
                    # Calculate average importance
                    importance = memory.get('metadata', {}).get('importance_level', 0)
                    if importance > 0:
                        total_importance += importance
                        importance_count += 1
                        
                        # Count highly important memories
                        if importance >= 8.0:
                            highly_accessed += 1
            except Exception as e:
                logger.warning(f"Error processing memory for stats: {e}")
                continue
        
        # Calculate average importance
        avg_importance = total_importance / importance_count if importance_count > 0 else 0.0
        
        # Memory health assessment
        memory_health = {
            "status": "healthy" if importance_count > 0 else "needs_attention",
            "avg_importance": avg_importance,
            "highly_accessed": highly_accessed,
            "scored_memories": importance_count,
            "unscored_memories": total_memories - importance_count
        }
        
        return MemoryStatsResponse(
            user_id=user_id,
            total_memories=total_memories,
            by_type=type_counts,
            average_importance=avg_importance,
            memory_health=memory_health
        )
        
    except Exception as e:
        logger.error(f"Error getting memory stats for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory statistics: {str(e)}")

@memory_router.post("/maintenance/{user_id}", response_model=MemoryMaintenanceResponse)
async def run_memory_maintenance(
    user_id: str = Path(..., description="User ID to run memory maintenance for")
):
    """Run memory maintenance for a specific user (matches /maintenance command from original agent)"""
    try:
        mem0_instance = get_mem0_instance()
        if not mem0_instance:
            raise HTTPException(status_code=500, detail="Memory system not initialized")
        
        # Get current memory count (same as original agent)
        search_results = mem0_instance.search("user", user_id=user_id)
        
        if isinstance(search_results, dict) and "results" in search_results:
            memories = search_results["results"]
        else:
            memories = search_results if search_results else []
        
        memory_count = len(memories)
        
        if memory_count == 0:
            return MemoryMaintenanceResponse(
                user_id=user_id,
                processed=0,
                promoted=0,
                demoted=0,
                cleaned=0,
                status="no_memories_found",
                memory_distribution={}
            )
        
        # Calculate memory type distribution (same as original agent)
        type_counts = {}
        for memory in memories:
            if isinstance(memory, dict):
                mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        # If we have the enhanced memory manager, use it
        memory_manager = get_memory_manager()
        if memory_manager:
            try:
                stats = memory_manager.run_memory_maintenance(user_id)
                
                return MemoryMaintenanceResponse(
                    user_id=user_id,
                    processed=stats.get("processed", memory_count),
                    promoted=stats.get("promoted", 0),
                    demoted=stats.get("demoted", 0),
                    cleaned=stats.get("cleaned", 0),
                    status="advanced_maintenance_completed",
                    memory_distribution=type_counts
                )
            except Exception as e:
                logger.warning(f"Enhanced memory maintenance failed: {e}")
                # Fall through to basic maintenance
        
        # Basic maintenance - same as original agent
        logger.info(f"Basic maintenance completed for {user_id}: {memory_count} memories, types: {type_counts}")
        
        return MemoryMaintenanceResponse(
            user_id=user_id,
            processed=memory_count,
            promoted=0,
            demoted=0,
            cleaned=0,
            status="basic_maintenance_completed",
            memory_distribution=type_counts
        )
        
    except Exception as e:
        logger.error(f"Error running memory maintenance for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run memory maintenance: {str(e)}")

@memory_router.get("/memories/{user_id}", response_model=MemoriesListResponse)
async def get_memories(
    user_id: str = Path(..., description="User ID to list memories for"),
    memory_type: str = Query("all", description="Memory type filter: all, core, long, short, working"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of memories to return")
):
    """List memories for a specific user (matches /memories command from original agent)"""
    try:
        mem0_instance = get_mem0_instance()
        if not mem0_instance:
            raise HTTPException(status_code=500, detail="Memory system not initialized")
        
        # Get memories using search (same logic as original agent)
        if memory_type == "all":
            # Get all memories using a broad search
            search_results = mem0_instance.search("user", user_id=user_id)
        else:
            # Search for specific type
            search_results = mem0_instance.search(memory_type, user_id=user_id)
        
        # Process search results (same as original agent)
        if isinstance(search_results, dict) and "results" in search_results:
            memories = search_results["results"]
        else:
            memories = search_results if search_results else []
        
        if not memories:
            return MemoriesListResponse(
                user_id=user_id,
                memory_type_filter=memory_type,
                total_found=0,
                showing=0,
                memories=[]
            )
        
        # Filter by type if specified (same logic as original agent)
        filtered_memories = []
        for memory in memories:
            try:
                if isinstance(memory, dict):
                    mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                    
                    # Filter by requested type (same logic as original agent)
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
            except Exception as e:
                logger.warning(f"Error processing memory: {e}")
                continue
        
        # Limit results and format response
        limited_memories = filtered_memories[:limit]
        
        formatted_memories = []
        for memory in limited_memories:
            mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
            importance = memory.get('metadata', {}).get('importance_level', 0)
            content = memory.get('memory', '')
            
            formatted_memories.append(MemoryItem(
                id=memory.get('id', 'unknown'),
                content=content,
                type=mem_type,
                importance=importance,
                metadata=memory.get('metadata', {})
            ))
        
        return MemoriesListResponse(
            user_id=user_id,
            memory_type_filter=memory_type,
            total_found=len(filtered_memories),
            showing=len(formatted_memories),
            memories=formatted_memories
        )
        
    except Exception as e:
        logger.error(f"Error listing memories for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list memories: {str(e)}")

@memory_router.delete("/clear/{user_id}")
async def clear_user_memories(
    user_id: str = Path(..., description="User ID to clear memories for"),
    memory_type: Optional[str] = Query(None, description="Memory type to clear (all if not specified)")
):
    """Clear memories for a specific user (use with caution!)"""
    try:
        mem0_instance = get_mem0_instance()
        if not mem0_instance:
            raise HTTPException(status_code=500, detail="Memory system not initialized")
        
        # Get current memories
        search_results = mem0_instance.search("user", user_id=user_id)
        
        if isinstance(search_results, dict) and "results" in search_results:
            memories = search_results["results"]
        else:
            memories = search_results if search_results else []
        
        if not memories:
            return {
                "user_id": user_id,
                "cleared_count": 0,
                "status": "no_memories_found"
            }
        
        # Filter by type if specified
        memories_to_delete = []
        if memory_type and memory_type != "all":
            for memory in memories:
                if isinstance(memory, dict):
                    mem_type = memory.get('metadata', {}).get('memory_type', 'unknown')
                    if memory_type == mem_type:
                        memories_to_delete.append(memory)
        else:
            memories_to_delete = memories
        
        # Delete memories
        deleted_count = 0
        for memory in memories_to_delete:
            try:
                memory_id = memory.get('id')
                if memory_id:
                    mem0_instance.delete(memory_id)
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete memory {memory.get('id', 'unknown')}: {e}")
                continue
        
        return {
            "user_id": user_id,
            "cleared_count": deleted_count,
            "memory_type_filter": memory_type or "all",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error clearing memories for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear memories: {str(e)}")

# Export the router
__all__ = ["memory_router"]
