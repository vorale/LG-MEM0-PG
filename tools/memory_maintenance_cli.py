#!/usr/bin/env python3
"""
Memory Maintenance CLI Tool
===========================

A standalone command-line tool for running memory maintenance operations
on the Mem0-based memory system.

Usage:
    python memory_maintenance_cli.py [options]
    ./memory_maintenance_cli.py [options]

Examples:
    # Run maintenance for default user
    python memory_maintenance_cli.py

    # Run maintenance for specific user
    python memory_maintenance_cli.py --user john_doe

    # Run maintenance for all users
    python memory_maintenance_cli.py --all-users

    # Show statistics only (no maintenance)
    python memory_maintenance_cli.py --stats-only

    # Verbose output
    python memory_maintenance_cli.py --verbose

    # Dry run (show what would be done)
    python memory_maintenance_cli.py --dry-run

Author: AI Assistant
Date: 2025-01-31
"""

import os
import sys
import argparse
import uuid
import warnings
from datetime import datetime
from typing import List, Dict, Any

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

try:
    import sys
    import os
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mem0 import Memory
    from src.core.memory_manager import Mem0MemoryManager, MemoryType
    from dotenv import load_dotenv
    import boto3
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required packages are installed:")
    print("  pip install mem0ai python-dotenv boto3")
    sys.exit(1)

# Load environment variables
load_dotenv()

class MemoryMaintenanceCLI:
    """Command-line interface for memory maintenance operations"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.memory_manager = None
        self._initialize_memory_manager()
    
    def _initialize_memory_manager(self):
        """Initialize the memory manager"""
        
        try:
            if self.verbose:
                print("🔧 Initializing memory manager...")
            
            # Fix telemetry by monkey patching posthog client
            try:
                import mem0.memory.telemetry
                import posthog.client
                
                original_capture = posthog.client.Client.capture
                
                def patched_capture(self, distinct_id=None, event=None, properties=None, **kwargs):
                    if distinct_id is None:
                        distinct_id = str(uuid.uuid4())
                    return original_capture(self, distinct_id, event, properties, **kwargs)
                
                posthog.client.Client.capture = patched_capture
                
                if self.verbose:
                    print("✅ PostHog client patched")
                    
            except ImportError:
                if self.verbose:
                    print("⚠️  Could not patch PostHog")
            
            # Verify AWS credentials
            try:
                test_client = boto3.client('sts', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))
                test_client.get_caller_identity()
                if self.verbose:
                    print("✅ AWS credentials verified")
            except Exception as e:
                print(f"❌ AWS credentials not available: {e}")
                print("Please configure AWS credentials using 'aws configure' or environment variables")
                sys.exit(1)
            
            # Initialize Mem0
            mem0_config = {
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
            }
            
            mem0 = Memory.from_config(mem0_config)
            
            # Initialize enhanced memory manager
            self.memory_manager = Mem0MemoryManager(mem0, config={
                "enable_llm_classification": True,
                "enable_automatic_promotion": True,
                "maintenance_interval_hours": 6
            })
            
            if self.verbose:
                print("✅ Memory manager initialized")
                
        except Exception as e:
            print(f"❌ Failed to initialize memory manager: {e}")
            sys.exit(1)
    
    def discover_users(self) -> List[str]:
        """Discover users who have memories in the system"""
        
        if self.verbose:
            print("🔍 Discovering users with memories...")
        
        # In a real system, you'd query the database for distinct user_ids
        # For now, we'll check common user IDs
        potential_users = [
            "default_user",
            "test_user", 
            "admin",
            "demo_user",
            "user1",
            "user2"
        ]
        
        active_users = []
        for user_id in potential_users:
            try:
                if self.memory_manager.has_memories(user_id):
                    active_users.append(user_id)
                    if self.verbose:
                        count = self.memory_manager.get_memory_count(user_id)
                        print(f"  ✅ Found user: {user_id} ({count} memories)")
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠️  Error checking user {user_id}: {e}")
        
        return active_users
    
    def show_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Show detailed statistics for a user"""
        
        try:
            stats = self.memory_manager.get_memory_statistics(user_id)
            
            print(f"\n📊 Memory Statistics for {user_id}:")
            print("=" * 50)
            
            if stats.get("error"):
                print(f"❌ Error: {stats['error']}")
                return stats
            
            # Basic stats
            print(f"Total memories: {stats.get('total_memories', 0)}")
            
            # Memory type distribution
            by_type = stats.get('by_type', {})
            if by_type:
                print(f"\nMemory types:")
                for mem_type, count in by_type.items():
                    if count > 0:
                        print(f"  {mem_type}: {count}")
            
            # Memory health
            health = stats.get('memory_health', {})
            if health:
                print(f"\nMemory health:")
                print(f"  Average importance: {health.get('avg_importance', 0):.2f}")
                print(f"  Highly accessed: {health.get('highly_accessed', 0)}")
                print(f"  Stale memories: {health.get('stale_memories', 0)}")
            
            # Access patterns
            access = stats.get('access_patterns', {})
            if access:
                print(f"\nAccess patterns:")
                print(f"  Total accesses: {access.get('total_accesses', 0)}")
                print(f"  Average per memory: {access.get('avg_accesses_per_memory', 0):.1f}")
                print(f"  Most accessed: {access.get('most_accessed', 0)}")
            
            # Promotion stats
            promotion = stats.get('promotion_stats', {})
            if promotion and promotion.get('total_promotions', 0) > 0:
                print(f"\nPromotion statistics:")
                print(f"  Total promotions: {promotion.get('total_promotions', 0)}")
                breakdown = promotion.get('promotion_breakdown', {})
                if breakdown:
                    for reason, count in breakdown.items():
                        print(f"    {reason}: {count}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting statistics for {user_id}: {e}")
            return {"error": str(e)}
    
    def run_maintenance(self, user_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Run maintenance for a specific user"""
        
        try:
            if not self.memory_manager.has_memories(user_id):
                print(f"ℹ️  No memories found for {user_id}")
                return {"processed": 0, "message": "No memories found"}
            
            memory_count = self.memory_manager.get_memory_count(user_id)
            
            if dry_run:
                print(f"🔍 [DRY RUN] Would process {memory_count} memories for {user_id}")
                return {"processed": memory_count, "dry_run": True}
            
            print(f"🔧 Running maintenance for {user_id} ({memory_count} memories)...")
            
            start_time = datetime.now()
            stats = self.memory_manager.run_memory_maintenance(user_id)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            if stats.get("error"):
                print(f"❌ Maintenance failed: {stats['error']}")
                return stats
            
            # Display results
            processed = stats.get("processed", 0)
            promoted = stats.get("promoted", 0)
            expired = stats.get("expired", 0)
            errors = stats.get("errors", 0)
            
            print(f"✅ Maintenance completed in {duration:.2f}s:")
            print(f"  Processed: {processed}")
            print(f"  Promoted: {promoted}")
            print(f"  Expired: {expired}")
            if errors > 0:
                print(f"  Errors: {errors}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Maintenance failed for {user_id}: {e}")
            return {"error": str(e)}
    
    def run_batch_maintenance(self, user_ids: List[str], dry_run: bool = False) -> Dict[str, Any]:
        """Run maintenance for multiple users"""
        
        print(f"🔧 Running batch maintenance for {len(user_ids)} users...")
        
        total_stats = {
            "users_processed": 0,
            "total_memories": 0,
            "total_promoted": 0,
            "total_expired": 0,
            "total_errors": 0,
            "failed_users": []
        }
        
        for user_id in user_ids:
            try:
                print(f"\n--- Processing {user_id} ---")
                stats = self.run_maintenance(user_id, dry_run)
                
                if stats.get("error"):
                    total_stats["failed_users"].append(user_id)
                else:
                    total_stats["users_processed"] += 1
                    total_stats["total_memories"] += stats.get("processed", 0)
                    total_stats["total_promoted"] += stats.get("promoted", 0)
                    total_stats["total_expired"] += stats.get("expired", 0)
                    total_stats["total_errors"] += stats.get("errors", 0)
                    
            except Exception as e:
                print(f"❌ Failed to process {user_id}: {e}")
                total_stats["failed_users"].append(user_id)
        
        # Summary
        print(f"\n📊 Batch Maintenance Summary:")
        print("=" * 40)
        print(f"Users processed: {total_stats['users_processed']}/{len(user_ids)}")
        print(f"Total memories: {total_stats['total_memories']}")
        print(f"Total promoted: {total_stats['total_promoted']}")
        print(f"Total expired: {total_stats['total_expired']}")
        
        if total_stats["total_errors"] > 0:
            print(f"Total errors: {total_stats['total_errors']}")
        
        if total_stats["failed_users"]:
            print(f"Failed users: {', '.join(total_stats['failed_users'])}")
        
        return total_stats


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Memory Maintenance CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run maintenance for default user
  %(prog)s --user john_doe          # Run maintenance for specific user
  %(prog)s --all-users              # Run maintenance for all users
  %(prog)s --stats-only             # Show statistics only
  %(prog)s --verbose                # Verbose output
  %(prog)s --dry-run                # Show what would be done
        """
    )
    
    parser.add_argument(
        "--user", "-u",
        type=str,
        default="default_user",
        help="User ID to run maintenance for (default: default_user)"
    )
    
    parser.add_argument(
        "--all-users", "-a",
        action="store_true",
        help="Run maintenance for all users with memories"
    )
    
    parser.add_argument(
        "--stats-only", "-s",
        action="store_true",
        help="Show statistics only, don't run maintenance"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--discover-users",
        action="store_true",
        help="Discover and list all users with memories"
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    print("🧠 Memory Maintenance CLI Tool")
    print("=" * 40)
    
    cli = MemoryMaintenanceCLI(verbose=args.verbose)
    
    try:
        if args.discover_users:
            # Discover users
            users = cli.discover_users()
            print(f"\n👥 Found {len(users)} users with memories:")
            for user_id in users:
                count = cli.memory_manager.get_memory_count(user_id)
                print(f"  - {user_id}: {count} memories")
            
        elif args.all_users:
            # Run for all users
            users = cli.discover_users()
            if not users:
                print("ℹ️  No users with memories found")
                return
            
            if args.stats_only:
                for user_id in users:
                    cli.show_user_statistics(user_id)
            else:
                cli.run_batch_maintenance(users, dry_run=args.dry_run)
                
        else:
            # Run for specific user
            user_id = args.user
            
            if args.stats_only:
                cli.show_user_statistics(user_id)
            else:
                cli.run_maintenance(user_id, dry_run=args.dry_run)
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
