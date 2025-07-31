"""
Mem0-Based Memory Manager with Promotion Logic
==============================================

This module provides an intelligent memory management layer on top of Mem0 that implements:
- LLM-powered memory type classification
- Access-based memory promotion (working → short_term → long_term → core)
- Automatic memory maintenance and consolidation
- Semantic understanding for memory updates and contradictions

Uses Mem0's native features:
- Metadata storage for memory types
- LLM-based classification and understanding
- Automatic memory consolidation and deduplication
- Built-in contradiction handling

Author: AI Assistant
Date: 2025-01-31
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Memory type classifications for promotion system"""
    WORKING = "working"        # Immediate conversation context (minutes to hours)
    SHORT_TERM = "short_term"  # Recent interactions (hours to days)
    LONG_TERM = "long_term"    # Persistent knowledge (days to months)
    CORE = "core"              # Fundamental user traits (permanent)


class PromotionReason(Enum):
    """Reasons for memory promotion"""
    ACCESS_COUNT = "access_count_threshold"
    REINFORCEMENT = "reinforcement_threshold"
    IMPORTANCE_BOOST = "importance_boost"
    TIME_BASED = "time_based_promotion"
    LLM_CLASSIFICATION = "llm_reclassification"


@dataclass
class PromotionRule:
    """Rules for memory promotion between types"""
    from_type: MemoryType
    to_type: MemoryType
    access_threshold: int
    min_importance: float = 0.0
    min_reinforcement: int = 0
    min_age_hours: float = 0.0
    additional_conditions: Optional[callable] = None


class Mem0MemoryManager:
    """
    Intelligent memory manager built on top of Mem0
    
    Features:
    - LLM-powered memory type classification
    - Access-based promotion system
    - Automatic memory maintenance
    - Semantic contradiction handling
    - Memory lifecycle management
    """
    
    def __init__(self, mem0_instance, config: Optional[Dict] = None):
        """
        Initialize the Mem0-based memory manager
        
        Args:
            mem0_instance: Initialized Mem0 Memory instance
            config: Configuration dictionary for memory management
        """
        self.mem0 = mem0_instance
        
        # Default configuration
        self.config = {
            "promotion_rules": self._get_default_promotion_rules(),
            "importance_thresholds": {
                MemoryType.WORKING: 1.0,
                MemoryType.SHORT_TERM: 3.0,
                MemoryType.LONG_TERM: 5.0,
                MemoryType.CORE: 8.0
            },
            "decay_rates": {
                MemoryType.WORKING: 0.8,      # High decay
                MemoryType.SHORT_TERM: 0.3,   # Medium decay
                MemoryType.LONG_TERM: 0.05,   # Low decay
                MemoryType.CORE: 0.01         # Very low decay
            },
            "max_age_hours": {
                MemoryType.WORKING: 24,       # 1 day
                MemoryType.SHORT_TERM: 168,   # 1 week
                MemoryType.LONG_TERM: 8760,   # 1 year
                MemoryType.CORE: float('inf') # Permanent
            },
            "enable_llm_classification": True,
            "enable_automatic_promotion": True,
            "maintenance_interval_hours": 6
        }
        
        # Update with user config
        if config:
            self._update_config(config)
        
        logger.info("Mem0MemoryManager initialized with LLM-powered classification")
    
    def _get_default_promotion_rules(self) -> List[PromotionRule]:
        """Get default promotion rules"""
        return [
            PromotionRule(
                from_type=MemoryType.WORKING,
                to_type=MemoryType.SHORT_TERM,
                access_threshold=3,
                min_reinforcement=2,
                min_age_hours=1.0
            ),
            PromotionRule(
                from_type=MemoryType.SHORT_TERM,
                to_type=MemoryType.LONG_TERM,
                access_threshold=7,
                min_importance=5.0,
                min_reinforcement=3,
                min_age_hours=24.0
            ),
            PromotionRule(
                from_type=MemoryType.LONG_TERM,
                to_type=MemoryType.CORE,
                access_threshold=15,
                min_importance=8.0,
                min_reinforcement=5,
                min_age_hours=168.0  # 1 week
            )
        ]
    
    def _update_config(self, user_config: Dict):
        """Update configuration with user settings"""
        for key, value in user_config.items():
            if key in self.config:
                if isinstance(self.config[key], dict) and isinstance(value, dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value
    
    def add_memory_with_type(self, content: str, user_id: str, 
                           memory_type: Optional[MemoryType] = None,
                           context: Optional[Dict] = None,
                           importance_override: Optional[float] = None) -> Dict[str, Any]:
        """
        Add memory with automatic or manual type classification
        
        Args:
            content: Memory content
            user_id: User identifier
            memory_type: Optional manual memory type
            context: Optional context information
            importance_override: Optional importance score override
            
        Returns:
            Dictionary with memory addition result
        """
        logger.info(f"Adding memory for user {user_id}: {content[:50]}...")
        
        try:
            # Classify memory type using LLM if not specified
            if memory_type is None and self.config["enable_llm_classification"]:
                memory_type = self._classify_memory_type_with_llm(content, context)
            elif memory_type is None:
                memory_type = self._classify_memory_type_fallback(content)
            
            # Calculate importance score
            if importance_override is not None:
                importance = importance_override
            else:
                importance = self._calculate_importance_score(content, memory_type, context)
            
            # Create comprehensive metadata
            metadata = {
                "memory_type": memory_type.value,
                "importance_level": importance,
                "access_count": 0,
                "reinforcement_count": 1,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "last_reinforced": datetime.now().isoformat(),
                "promotion_eligible": True,
                "promotion_history": [],
                "decay_rate": self.config["decay_rates"][memory_type],
                "source": "user_input",
                "version": "1.0"
            }
            
            # Add context information
            if context:
                metadata["context"] = context
                if "conversation_id" in context:
                    metadata["conversation_id"] = context["conversation_id"]
                if "session_id" in context:
                    metadata["session_id"] = context["session_id"]
            
            # Store in Mem0 (it will handle deduplication and consolidation)
            result = self.mem0.add(content, user_id=user_id, metadata=metadata)
            
            logger.info(f"Memory stored with type: {memory_type.value}, importance: {importance:.2f}")
            
            return {
                "success": True,
                "memory_id": self._extract_memory_id(result),
                "memory_type": memory_type.value,
                "importance_score": importance,
                "metadata": metadata,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to add memory: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": content[:100]
            }
    
    def _classify_memory_type_with_llm(self, content: str, context: Optional[Dict] = None) -> MemoryType:
        """Use Mem0's LLM to classify memory type"""
        
        # Create a classification prompt
        classification_prompt = f"""
        Analyze this memory and classify it into one of these types based on its characteristics:

        MEMORY TYPES:
        1. working: Immediate conversation context, temporary references, current task state
           - Examples: "we were discussing", "you mentioned earlier", "let me continue"
           - Indicators: conversation references, immediate context, temporary states

        2. short_term: Recent events, current preferences, temporary information
           - Examples: "today I feel", "this week I'm working on", "currently I prefer"
           - Indicators: temporal words (today, recently, currently), temporary states

        3. long_term: Stable preferences, established facts, persistent information
           - Examples: "I like programming", "I work as engineer", "I live in Beijing"
           - Indicators: stable preferences, job info, location, established habits

        4. core: Fundamental identity, permanent traits, core beliefs, unchanging facts
           - Examples: "My name is", "I am a", "I believe in", "I always", "I never"
           - Indicators: identity markers, core beliefs, permanent characteristics

        MEMORY TO CLASSIFY: "{content}"
        
        CONTEXT: {json.dumps(context) if context else "None"}

        CLASSIFICATION RULES:
        - Look for temporal indicators (today, always, never, currently)
        - Consider personal significance (I am, I believe, my name)
        - Check for conversation markers (we discussed, you said)
        - Assess stability (likely to change vs permanent)
        - Consider the depth of personal information

        Respond with ONLY the classification: working, short_term, long_term, or core
        """
        
        try:
            # Use a temporary system user to get LLM classification
            temp_user_id = f"classifier_{uuid.uuid4().hex[:8]}"
            
            # Add classification request to Mem0
            classification_result = self.mem0.add(
                classification_prompt, 
                user_id=temp_user_id,
                metadata={"type": "classification_request", "temporary": True}
            )
            
            # Search for the classification result
            search_results = self.mem0.search("working short_term long_term core", user_id=temp_user_id)
            
            if isinstance(search_results, dict) and "results" in search_results:
                results = search_results["results"]
            else:
                results = search_results or []
            
            # Extract classification from results
            classification = self._extract_classification_from_results(results, content)
            
            # Clean up temporary memories
            self._cleanup_temporary_memories(temp_user_id)
            
            logger.info(f"LLM classified '{content[:30]}...' as {classification.value}")
            return classification
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}, using fallback")
            return self._classify_memory_type_fallback(content)
    
    def _extract_classification_from_results(self, results: List[Dict], original_content: str) -> MemoryType:
        """Extract memory type classification from LLM results"""
        
        if not results:
            return self._classify_memory_type_fallback(original_content)
        
        # Look for classification keywords in the results
        classification_text = ""
        for result in results:
            memory_content = result.get('memory', '')
            if any(keyword in memory_content.lower() for keyword in ['working', 'short_term', 'long_term', 'core']):
                classification_text = memory_content.lower()
                break
        
        # Extract the classification
        if 'core' in classification_text:
            return MemoryType.CORE
        elif 'long_term' in classification_text or 'long-term' in classification_text:
            return MemoryType.LONG_TERM
        elif 'short_term' in classification_text or 'short-term' in classification_text:
            return MemoryType.SHORT_TERM
        elif 'working' in classification_text:
            return MemoryType.WORKING
        else:
            return self._classify_memory_type_fallback(original_content)
    
    def _classify_memory_type_fallback(self, content: str) -> MemoryType:
        """Fallback rule-based classification when LLM fails"""
        
        content_lower = content.lower()
        
        # Core identity patterns
        core_patterns = [
            r'\b(my name is|i am|i was born|i believe|i always|i never)\b',
            r'\b(我叫|我是|我出生|我相信|我总是|我从不)\b'
        ]
        
        # Long-term preference patterns
        long_term_patterns = [
            r'\b(i like|i love|i prefer|i enjoy|i work|i live)\b',
            r'\b(我喜欢|我爱|我更喜欢|我享受|我工作|我住在)\b'
        ]
        
        # Short-term context patterns
        short_term_patterns = [
            r'\b(today|yesterday|this week|currently|recently|lately)\b',
            r'\b(今天|昨天|这周|目前|最近|近来)\b'
        ]
        
        # Working memory patterns
        working_patterns = [
            r'\b(we were|you mentioned|as we discussed|earlier|just now)\b',
            r'\b(我们刚才|你提到|正如我们讨论|之前|刚刚)\b'
        ]
        
        # Check patterns in order of priority
        for pattern in core_patterns:
            if re.search(pattern, content_lower):
                return MemoryType.CORE
        
        for pattern in long_term_patterns:
            if re.search(pattern, content_lower):
                return MemoryType.LONG_TERM
        
        for pattern in short_term_patterns:
            if re.search(pattern, content_lower):
                return MemoryType.SHORT_TERM
        
        for pattern in working_patterns:
            if re.search(pattern, content_lower):
                return MemoryType.WORKING
        
        # Default based on content characteristics
        if len(content) < 20:
            return MemoryType.WORKING
        elif any(word in content_lower for word in ['always', 'never', 'every', 'all']):
            return MemoryType.LONG_TERM
        else:
            return MemoryType.SHORT_TERM
    
    def _calculate_importance_score(self, content: str, memory_type: MemoryType, 
                                  context: Optional[Dict] = None) -> float:
        """Calculate importance score for memory"""
        
        base_scores = {
            MemoryType.CORE: 9.0,
            MemoryType.LONG_TERM: 6.0,
            MemoryType.SHORT_TERM: 4.0,
            MemoryType.WORKING: 2.0
        }
        
        score = base_scores[memory_type]
        content_lower = content.lower()
        
        # Personal pronoun bonus
        personal_count = content_lower.count('i ') + content_lower.count('my ') + content_lower.count('me ')
        personal_count += content_lower.count('我') + content_lower.count('我的')
        score += min(personal_count * 0.3, 1.5)
        
        # Emotional content bonus
        emotional_words = ['love', 'hate', 'excited', 'worried', 'happy', 'sad', 'angry', 'afraid']
        emotional_words_cn = ['喜欢', '讨厌', '兴奋', '担心', '开心', '难过', '生气', '害怕']
        emotion_count = sum(1 for word in emotional_words + emotional_words_cn if word in content_lower)
        score += min(emotion_count * 0.4, 2.0)
        
        # Length bonus
        if len(content) > 50:
            score += 0.5
        if len(content) > 100:
            score += 0.5
        
        # Context bonus
        if context:
            if context.get('user_correction'):
                score += 1.0  # User corrections are important
            if context.get('repeated_mention'):
                score += 0.5  # Repeated mentions are more important
        
        return max(1.0, min(10.0, score))
    
    def search_with_promotion(self, query: str, user_id: str, 
                            memory_types: Optional[List[MemoryType]] = None,
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories and handle promotion based on access patterns
        
        Args:
            query: Search query
            user_id: User identifier
            memory_types: Optional filter by memory types
            max_results: Maximum number of results
            
        Returns:
            List of memory dictionaries with updated access counts
        """
        logger.info(f"Searching memories for user {user_id}: {query}")
        
        try:
            # Get memories from Mem0
            if memory_types:
                # Filter by memory type using metadata
                all_memories = self.mem0.get_all(user_id=user_id)
                if not all_memories:
                    return []
                
                type_values = [mt.value for mt in memory_types]
                memories = []
                
                for memory in all_memories:
                    try:
                        processed_memory = self._process_memory(memory)
                        mem_type = processed_memory.get('metadata', {}).get('memory_type', 'working')
                        
                        if mem_type in type_values:
                            # Apply search filtering manually if query provided
                            if query.strip():
                                memory_content = processed_memory.get('memory', '').lower()
                                if query.lower() in memory_content:
                                    memories.append(processed_memory)
                            else:
                                memories.append(processed_memory)
                    except Exception as e:
                        logger.error(f"Error processing memory in search filter: {str(e)}")
                        continue
            else:
                # Use Mem0's search
                search_results = self.mem0.search(query, user_id=user_id)
                if isinstance(search_results, dict) and "results" in search_results:
                    raw_memories = search_results["results"]
                else:
                    raw_memories = search_results or []
                
                # Process all memories safely
                memories = []
                for memory in raw_memories:
                    try:
                        processed_memory = self._process_memory(memory)
                        memories.append(processed_memory)
                    except Exception as e:
                        logger.error(f"Error processing memory in search results: {str(e)}")
                        continue
            
            # Process each memory for promotion
            processed_memories = []
            for memory in memories[:max_results]:
                try:
                    processed_memory = self._process_memory_access(memory, user_id)
                    processed_memories.append(processed_memory)
                except Exception as e:
                    logger.error(f"Error processing memory access: {str(e)}")
                    # Still include the memory even if access processing fails
                    processed_memories.append(memory)
            
            logger.info(f"Retrieved and processed {len(processed_memories)} memories")
            return processed_memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {str(e)}")
            return []
    
    def _process_memory_access(self, memory: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process memory access and check for promotion"""
        
        try:
            # Ensure memory is properly processed
            processed_memory = self._process_memory(memory)
            metadata = processed_memory.get('metadata', {})
            
            current_type = MemoryType(metadata.get('memory_type', 'working'))
            access_count = metadata.get('access_count', 0) + 1
            
            # Update access metadata
            metadata['access_count'] = access_count
            metadata['last_accessed'] = datetime.now().isoformat()
            
            # Check for promotion if enabled
            if self.config["enable_automatic_promotion"]:
                promotion_result = self._check_and_apply_promotion(processed_memory, metadata, user_id)
                if promotion_result:
                    metadata.update(promotion_result)
            
            # Update memory in Mem0
            self._update_memory_metadata(processed_memory, metadata, user_id)
            
            # Update the memory object
            processed_memory['metadata'] = metadata
            
            return processed_memory
            
        except Exception as e:
            logger.error(f"Failed to process memory access: {str(e)}")
            # Return the original memory if processing fails
            return self._process_memory(memory)
    
    def _check_and_apply_promotion(self, memory: Dict[str, Any], metadata: Dict[str, Any], 
                                 user_id: str) -> Optional[Dict[str, Any]]:
        """Check if memory should be promoted and apply promotion"""
        
        current_type = MemoryType(metadata.get('memory_type', 'working'))
        
        # Find applicable promotion rule
        for rule in self.config["promotion_rules"]:
            if rule.from_type != current_type:
                continue
            
            # Check all conditions
            if not self._check_promotion_conditions(metadata, rule):
                continue
            
            # Apply promotion
            logger.info(f"Promoting memory from {current_type.value} to {rule.to_type.value}")
            
            promotion_info = {
                'memory_type': rule.to_type.value,
                'promoted_at': datetime.now().isoformat(),
                'promotion_reason': PromotionReason.ACCESS_COUNT.value,
                'previous_type': current_type.value,
                'decay_rate': self.config["decay_rates"][rule.to_type]
            }
            
            # Update promotion history
            promotion_history = metadata.get('promotion_history', [])
            promotion_history.append(promotion_info)
            promotion_info['promotion_history'] = promotion_history
            
            return promotion_info
        
        return None
    
    def _check_promotion_conditions(self, metadata: Dict[str, Any], rule: PromotionRule) -> bool:
        """Check if all promotion conditions are met"""
        
        access_count = metadata.get('access_count', 0)
        importance = metadata.get('importance_level', 0)
        reinforcement = metadata.get('reinforcement_count', 0)
        
        # Check basic thresholds
        if access_count < rule.access_threshold:
            return False
        
        if importance < rule.min_importance:
            return False
        
        if reinforcement < rule.min_reinforcement:
            return False
        
        # Check age requirement
        if rule.min_age_hours > 0:
            created_at = metadata.get('created_at')
            if created_at:
                age_hours = self._calculate_age_hours(created_at)
                if age_hours < rule.min_age_hours:
                    return False
        
        # Check additional conditions
        if rule.additional_conditions and not rule.additional_conditions(metadata):
            return False
        
        return True
    
    def reinforce_memory(self, memory_content: str, user_id: str, 
                        boost_amount: float = 0.5) -> bool:
        """
        Reinforce a memory by increasing its importance and reinforcement count
        
        Args:
            memory_content: Content to search for and reinforce
            user_id: User identifier
            boost_amount: Amount to boost importance score
            
        Returns:
            Success status
        """
        logger.info(f"Reinforcing memory for user {user_id}: {memory_content[:50]}...")
        
        try:
            # Search for the memory
            search_results = self.mem0.search(memory_content, user_id=user_id)
            if isinstance(search_results, dict) and "results" in search_results:
                raw_memories = search_results["results"]
            else:
                raw_memories = search_results or []
            
            if not raw_memories:
                logger.warning(f"No memory found to reinforce: {memory_content[:50]}...")
                return False
            
            # Process and reinforce the most relevant memory
            try:
                target_memory = self._process_memory(raw_memories[0])  # Most relevant match
                metadata = target_memory.get('metadata', {})
                
                # Update reinforcement data
                metadata['reinforcement_count'] = metadata.get('reinforcement_count', 0) + 1
                metadata['last_reinforced'] = datetime.now().isoformat()
                
                # Boost importance
                current_importance = metadata.get('importance_level', 5.0)
                metadata['importance_level'] = min(10.0, current_importance + boost_amount)
                
                # Re-add to Mem0 (it will update/consolidate automatically)
                self.mem0.add(memory_content, user_id=user_id, metadata=metadata)
                
                logger.info(f"Memory reinforced: {memory_content[:50]}...")
                return True
                
            except Exception as e:
                logger.error(f"Error processing memory for reinforcement: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to reinforce memory: {str(e)}")
            return False
    
    def get_memories_by_type(self, user_id: str, memory_types: List[MemoryType], 
                           min_importance: float = 0.0, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get memories filtered by type and importance
        
        Args:
            user_id: User identifier
            memory_types: List of memory types to include
            min_importance: Minimum importance threshold
            max_results: Maximum number of results
            
        Returns:
            List of filtered memories
        """
        logger.info(f"Getting memories by type for user {user_id}: {[mt.value for mt in memory_types]}")
        
        try:
            # Get all memories
            all_memories = self.mem0.get_all(user_id=user_id)
            if not all_memories:
                return []
            
            # Filter by type and importance
            type_values = [mt.value for mt in memory_types]
            filtered_memories = []
            
            for memory in all_memories:
                try:
                    # Process memory safely
                    processed_memory = self._process_memory(memory)
                    metadata = processed_memory.get('metadata', {})
                    
                    mem_type = metadata.get('memory_type', 'working')
                    importance = metadata.get('importance_level', 0)
                    
                    if mem_type in type_values and importance >= min_importance:
                        filtered_memories.append(processed_memory)
                        
                except Exception as e:
                    logger.error(f"Error processing memory in get_memories_by_type: {str(e)}")
                    continue
            
            # Sort by importance and recency
            filtered_memories.sort(key=lambda m: (
                m.get('metadata', {}).get('importance_level', 0),
                m.get('metadata', {}).get('last_accessed', '')
            ), reverse=True)
            
            # Limit results
            if max_results:
                filtered_memories = filtered_memories[:max_results]
            
            logger.info(f"Retrieved {len(filtered_memories)} memories by type")
            return filtered_memories
            
        except Exception as e:
            logger.error(f"Failed to get memories by type: {str(e)}")
            return []
    
    def get_working_memory(self, user_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get current conversation context (working memory)"""
        return self.get_memories_by_type(user_id, [MemoryType.WORKING], max_results=max_results)
    
    def get_short_term_memory(self, user_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions (short-term memory)"""
        return self.get_memories_by_type(user_id, [MemoryType.SHORT_TERM], max_results=max_results)
    
    def get_long_term_memory(self, user_id: str, min_importance: float = 5.0, 
                           max_results: int = 20) -> List[Dict[str, Any]]:
        """Get persistent knowledge (long-term memory)"""
        return self.get_memories_by_type(
            user_id, [MemoryType.LONG_TERM], 
            min_importance=min_importance, max_results=max_results
        )
    
    def get_core_memories(self, user_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get fundamental user traits (core memory)"""
        return self.get_memories_by_type(
            user_id, [MemoryType.CORE], 
            min_importance=8.0, max_results=max_results
        )
    
    def get_memory_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics about user's memories
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            # Get all memories using search instead of get_all
            all_memories = []
            search_terms = ["user", "conversation", "assistant", "I", "the"]
            
            for term in search_terms:
                try:
                    search_result = self.mem0.search(term, user_id=user_id)
                    if isinstance(search_result, dict) and "results" in search_result:
                        memories = search_result["results"]
                    else:
                        memories = search_result if search_result else []
                    
                    # Add unique memories (avoid duplicates by ID)
                    existing_ids = {m.get('id') for m in all_memories}
                    for memory in memories:
                        if memory.get('id') not in existing_ids:
                            all_memories.append(memory)
                            
                except Exception as e:
                    logger.debug(f"Search term '{term}' failed: {e}")
                    continue
            
            if not all_memories:
                return {"total_memories": 0}
            
            # Initialize statistics
            stats = {
                "total_memories": len(all_memories),
                "by_type": {mt.value: 0 for mt in MemoryType},
                "importance_distribution": [],
                "access_patterns": {
                    "total_accesses": 0,
                    "avg_accesses_per_memory": 0,
                    "most_accessed": 0
                },
                "promotion_stats": {
                    "total_promotions": 0,
                    "promotion_breakdown": {}
                },
                "memory_health": {
                    "avg_importance": 0,
                    "stale_memories": 0,
                    "highly_accessed": 0
                }
            }
            
            total_importance = 0
            total_accesses = 0
            processed_count = 0
            
            for memory in all_memories:
                try:
                    # Process memory safely
                    processed_memory = self._process_memory(memory)
                    metadata = processed_memory.get('metadata', {})
                    processed_count += 1
                    
                    # Type distribution
                    memory_type = metadata.get('memory_type', 'working')
                    if memory_type in stats["by_type"]:
                        stats["by_type"][memory_type] += 1
                    else:
                        stats["by_type"][memory_type] = 1
                    
                    # Importance distribution
                    importance = metadata.get('importance_level', 0)
                    total_importance += importance
                    stats["importance_distribution"].append(importance)
                    
                    # Access patterns
                    access_count = metadata.get('access_count', 0)
                    total_accesses += access_count
                    stats["access_patterns"]["most_accessed"] = max(
                        stats["access_patterns"]["most_accessed"], access_count
                    )
                    
                    # Promotion statistics
                    promotion_history = metadata.get('promotion_history', [])
                    stats["promotion_stats"]["total_promotions"] += len(promotion_history)
                    
                    for promotion in promotion_history:
                        reason = promotion.get('promotion_reason', 'unknown')
                        stats["promotion_stats"]["promotion_breakdown"][reason] = \
                            stats["promotion_stats"]["promotion_breakdown"].get(reason, 0) + 1
                    
                    # Memory health
                    if access_count > 10:
                        stats["memory_health"]["highly_accessed"] += 1
                    
                    last_accessed = metadata.get('last_accessed')
                    if last_accessed:
                        hours_since_access = self._calculate_age_hours(last_accessed)
                        if hours_since_access > 168:  # 1 week
                            stats["memory_health"]["stale_memories"] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing memory in statistics: {str(e)}")
                    continue
            
            # Calculate averages
            if processed_count > 0:
                stats["memory_health"]["avg_importance"] = total_importance / processed_count
                stats["access_patterns"]["avg_accesses_per_memory"] = total_accesses / processed_count
                stats["access_patterns"]["total_accesses"] = total_accesses
            
            # Update total count to reflect actually processed memories
            stats["total_memories"] = processed_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {str(e)}")
            return {"error": str(e)}
    
    def run_memory_maintenance(self, user_id: str) -> Dict[str, Any]:
        """
        Run comprehensive memory maintenance
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with maintenance statistics
        """
        logger.info(f"Running memory maintenance for user {user_id}")
        
        try:
            # Get all memories using search instead of get_all
            # Use multiple search terms to get comprehensive results
            all_memories = []
            search_terms = ["user", "conversation", "assistant", "I", "the"]
            
            for term in search_terms:
                try:
                    search_result = self.mem0.search(term, user_id=user_id)
                    if isinstance(search_result, dict) and "results" in search_result:
                        memories = search_result["results"]
                    else:
                        memories = search_result if search_result else []
                    
                    # Add unique memories (avoid duplicates by ID)
                    existing_ids = {m.get('id') for m in all_memories}
                    for memory in memories:
                        if memory.get('id') not in existing_ids:
                            all_memories.append(memory)
                            
                except Exception as e:
                    logger.debug(f"Search term '{term}' failed: {e}")
                    continue
            
            if not all_memories:
                logger.info(f"No memories found for user {user_id}")
                return {"processed": 0, "promoted": 0, "expired": 0, "consolidated": 0}
            
            maintenance_stats = {
                "processed": len(all_memories),
                "promoted": 0,
                "expired": 0,
                "consolidated": 0,
                "errors": 0
            }
            
            expired_memory_ids = []
            
            for memory in all_memories:
                try:
                    # Process memory object safely
                    processed_memory = self._process_memory(memory)
                    metadata = processed_memory.get('metadata', {})
                    
                    # Check for pattern-based promotion
                    if self._should_promote_by_pattern(processed_memory):
                        promotion_result = self._check_and_apply_promotion(processed_memory, metadata, user_id)
                        if promotion_result:
                            self._update_memory_metadata(processed_memory, {**metadata, **promotion_result}, user_id)
                            maintenance_stats["promoted"] += 1
                    
                    # Check for expiration
                    if self._should_expire_memory(processed_memory):
                        memory_id = self._extract_memory_id_safe(processed_memory)
                        if memory_id:
                            expired_memory_ids.append(memory_id)
                            maintenance_stats["expired"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing memory during maintenance: {str(e)}")
                    maintenance_stats["errors"] += 1
            
            # Remove expired memories
            for memory_id in expired_memory_ids:
                try:
                    self.mem0.delete(memory_id)
                    logger.debug(f"Deleted expired memory: {memory_id}")
                except Exception as e:
                    logger.error(f"Failed to delete expired memory {memory_id}: {str(e)}")
            
            # Mem0 automatically handles consolidation when adding memories
            # so we don't need to do it manually
            
            logger.info(f"Memory maintenance completed: {maintenance_stats}")
            return maintenance_stats
            
        except Exception as e:
            logger.error(f"Failed to run memory maintenance: {str(e)}")
            return {"error": str(e), "processed": 0, "promoted": 0, "expired": 0}
    
    def _process_memory(self, memory: Any) -> Dict[str, Any]:
        """Process a raw memory from Mem0 into our standardized format"""
        
        if isinstance(memory, dict):
            # Already a dictionary, ensure it has required fields
            if 'metadata' not in memory:
                memory['metadata'] = {}
            return memory
        
        elif hasattr(memory, '__dict__'):
            # Convert object to dictionary
            memory_dict = {
                'id': getattr(memory, 'id', str(uuid.uuid4())),
                'memory': getattr(memory, 'memory', str(memory)),
                'metadata': getattr(memory, 'metadata', {}),
                'created_at': getattr(memory, 'created_at', datetime.now().isoformat()),
                'updated_at': getattr(memory, 'updated_at', datetime.now().isoformat())
            }
            
            # Ensure metadata is a dictionary
            if not isinstance(memory_dict['metadata'], dict):
                memory_dict['metadata'] = {}
            
            return memory_dict
        
        elif isinstance(memory, (list, tuple)):
            # Handle case where memory is a list/tuple
            if len(memory) > 0:
                return self._process_memory(memory[0])  # Process first item
            else:
                return {
                    'id': str(uuid.uuid4()),
                    'memory': '',
                    'metadata': {},
                    'created_at': datetime.now().isoformat()
                }
        
        else:
            # Handle other types by converting to string
            return {
                'id': str(uuid.uuid4()),
                'memory': str(memory),
                'metadata': {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
    
    def _extract_memory_id_safe(self, memory: Dict[str, Any]) -> Optional[str]:
        """Safely extract memory ID from memory object"""
        
        try:
            # Try different ways to get the ID
            if isinstance(memory, dict):
                return memory.get('id') or memory.get('_id') or memory.get('memory_id')
            elif hasattr(memory, 'id'):
                return str(memory.id)
            elif hasattr(memory, '_id'):
                return str(memory._id)
            else:
                logger.warning(f"Could not extract ID from memory: {type(memory)}")
                return None
        except Exception as e:
            logger.error(f"Error extracting memory ID: {str(e)}")
            return None
    
    def _should_promote_by_pattern(self, memory: Dict[str, Any]) -> bool:
        """Check if memory should be promoted based on usage patterns"""
        
        metadata = memory.get('metadata', {})
        memory_type = metadata.get('memory_type', 'working')
        access_count = metadata.get('access_count', 0)
        reinforcement_count = metadata.get('reinforcement_count', 0)
        importance = metadata.get('importance_level', 0)
        
        # Pattern-based promotion rules
        if memory_type == 'working':
            return access_count >= 3 and reinforcement_count >= 2
        elif memory_type == 'short_term':
            return access_count >= 7 and importance >= 5.0
        elif memory_type == 'long_term':
            return access_count >= 15 and importance >= 8.0
        
        return False
    
    def _should_expire_memory(self, memory: Dict[str, Any]) -> bool:
        """Check if memory should be expired based on age and usage"""
        
        metadata = memory.get('metadata', {})
        memory_type = MemoryType(metadata.get('memory_type', 'working'))
        
        # Check max age
        max_age = self.config["max_age_hours"][memory_type]
        if max_age != float('inf'):
            created_at = metadata.get('created_at')
            if created_at:
                age_hours = self._calculate_age_hours(created_at)
                if age_hours > max_age:
                    return True
        
        # Check importance threshold
        importance = metadata.get('importance_level', 0)
        min_importance = self.config["importance_thresholds"][memory_type]
        if importance < min_importance:
            return True
        
        return False
    
    def _update_memory_metadata(self, memory: Dict[str, Any], new_metadata: Dict[str, Any], user_id: str):
        """Update memory metadata using Mem0's update mechanism"""
        
        try:
            content = memory.get('memory', '')
            if content:
                # Re-add with updated metadata - Mem0 will handle the update
                self.mem0.add(content, user_id=user_id, metadata=new_metadata)
                logger.debug(f"Updated memory metadata for: {content[:30]}...")
            
        except Exception as e:
            logger.error(f"Failed to update memory metadata: {str(e)}")
    
    def _cleanup_temporary_memories(self, temp_user_id: str):
        """Clean up temporary memories created for classification"""
        
        try:
            temp_memories = self.mem0.get_all(user_id=temp_user_id)
            for memory in temp_memories:
                memory_id = memory.get('id')
                if memory_id:
                    self.mem0.delete(memory_id)
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary memories: {str(e)}")
    
    def _extract_memory_id(self, result: Any) -> str:
        """Extract memory ID from Mem0 result"""
        
        if isinstance(result, dict):
            return result.get('id', str(uuid.uuid4()))
        elif hasattr(result, 'id'):
            return result.id
        else:
            return str(uuid.uuid4())
    
    def has_memories(self, user_id: str) -> bool:
        """
        Check if a user has any memories
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has memories, False otherwise
        """
        try:
            # Use search with a common word that should match most memories
            # Avoid empty string which causes embedding validation errors
            search_result = self.mem0.search("user", user_id=user_id)
            
            # Handle different search result formats
            if isinstance(search_result, dict) and "results" in search_result:
                memories = search_result["results"]
            else:
                memories = search_result if search_result else []
            
            # Check if we have any valid memories
            if not memories:
                # Try alternative search terms
                for query in ["conversation", "assistant", "I", "the"]:
                    try:
                        search_result = self.mem0.search(query, user_id=user_id)
                        if isinstance(search_result, dict) and "results" in search_result:
                            memories = search_result["results"]
                        else:
                            memories = search_result if search_result else []
                        
                        if memories:
                            break
                    except:
                        continue
            
            return len(memories) > 0
            
        except Exception as e:
            # Log at debug level to avoid spam, but still track the issue
            logger.debug(f"Error checking if user {user_id} has memories: {str(e)}")
            return False
    
    def get_memory_count(self, user_id: str) -> int:
        """
        Get the count of memories for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of memories
        """
        try:
            # Use search with a common word that should match most memories
            search_result = self.mem0.search("user", user_id=user_id)
            
            # Handle different search result formats
            if isinstance(search_result, dict) and "results" in search_result:
                memories = search_result["results"]
            else:
                memories = search_result if search_result else []
            
            if not memories:
                # Try alternative search terms to get a more complete count
                all_memories = []
                for query in ["conversation", "assistant", "I", "the", "a"]:
                    try:
                        search_result = self.mem0.search(query, user_id=user_id)
                        if isinstance(search_result, dict) and "results" in search_result:
                            query_memories = search_result["results"]
                        else:
                            query_memories = search_result if search_result else []
                        
                        # Add unique memories (avoid duplicates by ID)
                        existing_ids = {m.get('id') for m in all_memories}
                        for memory in query_memories:
                            if memory.get('id') not in existing_ids:
                                all_memories.append(memory)
                        
                    except:
                        continue
                
                memories = all_memories
            
            return len(memories)
            
        except Exception as e:
            logger.debug(f"Error getting memory count for user {user_id}: {str(e)}")
            return 0
    
    def _calculate_age_hours(self, timestamp_str: str) -> float:
        """Calculate age in hours from timestamp string"""
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = datetime.now() - timestamp.replace(tzinfo=None)
            return age.total_seconds() / 3600
        except Exception:
            return 0.0
    
    # Convenience methods for common operations
    def add_conversation_context(self, content: str, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Add conversation context as working memory"""
        return self.add_memory_with_type(
            content, user_id, 
            memory_type=MemoryType.WORKING,
            context={"conversation_id": conversation_id, "type": "conversation_context"}
        )
    
    def add_user_preference(self, content: str, user_id: str, importance: float = 7.0) -> Dict[str, Any]:
        """Add user preference as long-term memory"""
        return self.add_memory_with_type(
            content, user_id,
            memory_type=MemoryType.LONG_TERM,
            importance_override=importance,
            context={"type": "user_preference"}
        )
    
    def add_core_identity(self, content: str, user_id: str) -> Dict[str, Any]:
        """Add core identity information"""
        return self.add_memory_with_type(
            content, user_id,
            memory_type=MemoryType.CORE,
            importance_override=9.0,
            context={"type": "core_identity"}
        )
    
    def get_conversation_context(self, user_id: str, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation-specific working memory"""
        working_memories = self.get_working_memory(user_id)
        return [m for m in working_memories 
                if m.get('metadata', {}).get('context', {}).get('conversation_id') == conversation_id]


# Example usage and testing
if __name__ == "__main__":
    print("Mem0 Memory Manager - Example Usage")
    print("===================================")
    
    # This would be used with your actual Mem0 instance
    # mem0_manager = Mem0MemoryManager(your_mem0_instance)
    
    print("\nExample memory classifications:")
    print("-" * 40)
    
    test_memories = [
        ("我喜欢臭鳜鱼", "User preference - should be LONG_TERM"),
        ("我的名字是张三", "Identity information - should be CORE"),
        ("我今天感觉很累", "Current state - should be SHORT_TERM"),
        ("我们刚才在讨论Python", "Conversation context - should be WORKING"),
        ("我总是喝咖啡而不是茶", "Permanent preference - should be CORE"),
        ("最近我在学习机器学习", "Current activity - should be SHORT_TERM")
    ]
    
    # Create a mock manager for demonstration
    class MockMem0Manager(Mem0MemoryManager):
        def __init__(self):
            self.config = {
                "enable_llm_classification": False,  # Use fallback for demo
                "enable_automatic_promotion": True,
                "promotion_rules": self._get_default_promotion_rules(),
                "importance_thresholds": {
                    MemoryType.WORKING: 1.0,
                    MemoryType.SHORT_TERM: 3.0,
                    MemoryType.LONG_TERM: 5.0,
                    MemoryType.CORE: 8.0
                },
                "decay_rates": {
                    MemoryType.WORKING: 0.8,
                    MemoryType.SHORT_TERM: 0.3,
                    MemoryType.LONG_TERM: 0.05,
                    MemoryType.CORE: 0.01
                },
                "max_age_hours": {
                    MemoryType.WORKING: 24,
                    MemoryType.SHORT_TERM: 168,
                    MemoryType.LONG_TERM: 8760,
                    MemoryType.CORE: float('inf')
                }
            }
    
    mock_manager = MockMem0Manager()
    
    for content, expected in test_memories:
        memory_type = mock_manager._classify_memory_type_fallback(content)
        importance = mock_manager._calculate_importance_score(content, memory_type)
        
        print(f"Memory: {content}")
        print(f"  Classified as: {memory_type.value}")
        print(f"  Importance: {importance:.1f}")
        print(f"  Expected: {expected}")
        print()
    
    print("Integration with your Mem0 instance:")
    print("mem0_manager = Mem0MemoryManager(your_mem0_instance)")
    print("result = mem0_manager.add_memory_with_type('我喜欢编程', 'user123')")
    print("memories = mem0_manager.search_with_promotion('编程', 'user123')")
    print("stats = mem0_manager.get_memory_statistics('user123')")
