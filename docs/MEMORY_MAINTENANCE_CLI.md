# Memory Maintenance CLI Tool

A standalone command-line tool for running memory maintenance operations on the Mem0-based memory system.

## 🚀 Quick Start

### Basic Usage
```bash
# Run maintenance for default user
./memory-maintenance

# Or use Python directly
python memory_maintenance_cli.py
```

### Installation Check
```bash
# Check if all dependencies are installed
python -c "import mem0, boto3; print('✅ All dependencies available')"
```

## 📋 Command Options

### User-Specific Operations
```bash
# Run maintenance for specific user
./memory-maintenance --user john_doe
./memory-maintenance -u john_doe

# Show statistics only (no maintenance)
./memory-maintenance --user john_doe --stats-only
./memory-maintenance -u john_doe -s
```

### Batch Operations
```bash
# Run maintenance for all users with memories
./memory-maintenance --all-users
./memory-maintenance -a

# Show statistics for all users
./memory-maintenance --all-users --stats-only
./memory-maintenance -a -s
```

### Discovery and Analysis
```bash
# Discover all users with memories
./memory-maintenance --discover-users

# Verbose output for debugging
./memory-maintenance --verbose
./memory-maintenance -v

# Dry run (show what would be done)
./memory-maintenance --dry-run
./memory-maintenance -d
```

## 🎯 Usage Examples

### Example 1: Basic Maintenance
```bash
$ ./memory-maintenance
🧠 Memory Maintenance CLI Tool
========================================
🔧 Running maintenance for default_user (5 memories)...
✅ Maintenance completed in 2.34s:
  Processed: 5
  Promoted: 1
  Expired: 0
```

### Example 2: User Discovery
```bash
$ ./memory-maintenance --discover-users
🧠 Memory Maintenance CLI Tool
========================================
🔍 Discovering users with memories...
  ✅ Found user: default_user (5 memories)
  ✅ Found user: john_doe (12 memories)

👥 Found 2 users with memories:
  - default_user: 5 memories
  - john_doe: 12 memories
```

### Example 3: Detailed Statistics
```bash
$ ./memory-maintenance --user john_doe --stats-only
🧠 Memory Maintenance CLI Tool
========================================

📊 Memory Statistics for john_doe:
==================================================
Total memories: 12

Memory types:
  working: 2
  short_term: 3
  long_term: 6
  core: 1

Memory health:
  Average importance: 6.45
  Highly accessed: 3
  Stale memories: 1

Access patterns:
  Total accesses: 47
  Average per memory: 3.9
  Most accessed: 12

Promotion statistics:
  Total promotions: 4
    access_count_threshold: 3
    reinforcement_threshold: 1
```

### Example 4: Batch Processing
```bash
$ ./memory-maintenance --all-users --verbose
🧠 Memory Maintenance CLI Tool
========================================
🔧 Initializing memory manager...
✅ AWS credentials verified
✅ PostHog client patched
✅ Memory manager initialized
🔍 Discovering users with memories...
  ✅ Found user: default_user (5 memories)
  ✅ Found user: john_doe (12 memories)
🔧 Running batch maintenance for 2 users...

--- Processing default_user ---
🔧 Running maintenance for default_user (5 memories)...
✅ Maintenance completed in 1.23s:
  Processed: 5
  Promoted: 0
  Expired: 1

--- Processing john_doe ---
🔧 Running maintenance for john_doe (12 memories)...
✅ Maintenance completed in 2.87s:
  Processed: 12
  Promoted: 2
  Expired: 0

📊 Batch Maintenance Summary:
========================================
Users processed: 2/2
Total memories: 17
Total promoted: 2
Total expired: 1
```

### Example 5: Dry Run
```bash
$ ./memory-maintenance --all-users --dry-run
🧠 Memory Maintenance CLI Tool
========================================
🔧 Running batch maintenance for 2 users...

--- Processing default_user ---
🔍 [DRY RUN] Would process 5 memories for default_user

--- Processing john_doe ---
🔍 [DRY RUN] Would process 12 memories for john_doe

📊 Batch Maintenance Summary:
========================================
Users processed: 2/2
Total memories: 17
Total promoted: 0
Total expired: 0
```

## 🔧 Command Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--user USER_ID` | `-u` | Run maintenance for specific user |
| `--all-users` | `-a` | Run maintenance for all users |
| `--stats-only` | `-s` | Show statistics only, no maintenance |
| `--dry-run` | `-d` | Show what would be done |
| `--verbose` | `-v` | Enable verbose output |
| `--discover-users` | | List all users with memories |
| `--help` | `-h` | Show help message |

## 🔄 Scheduled Maintenance

### Using Cron (Linux/macOS)
```bash
# Add to crontab for daily maintenance at 2 AM
0 2 * * * /path/to/lg-m0-psql/memory-maintenance --all-users >> /var/log/memory-maintenance.log 2>&1

# Weekly detailed maintenance with statistics
0 3 * * 0 /path/to/lg-m0-psql/memory-maintenance --all-users --verbose >> /var/log/memory-maintenance-weekly.log 2>&1
```

### Using Task Scheduler (Windows)
```powershell
# Create a scheduled task
schtasks /create /tn "Memory Maintenance" /tr "python C:\path\to\memory_maintenance_cli.py --all-users" /sc daily /st 02:00
```

## 📊 What the Tool Does

### Memory Maintenance Operations
1. **Memory Promotion**: Upgrades frequently accessed memories
   - `working` → `short_term` → `long_term` → `core`
   
2. **Memory Decay**: Reduces importance of unused memories
   - Applies decay rates based on memory type
   - Removes memories below importance threshold
   
3. **Memory Cleanup**: Removes expired or invalid memories
   - Checks age limits for each memory type
   - Validates memory content and metadata

4. **Statistics Collection**: Gathers comprehensive memory health metrics
   - Memory type distribution
   - Access patterns and usage statistics
   - Promotion history and trends

### Performance Metrics
- **Processing Speed**: ~2-5 seconds per user (depends on memory count)
- **Memory Types**: Handles all 4 memory types (working, short_term, long_term, core)
- **Batch Processing**: Efficient handling of multiple users
- **Error Handling**: Graceful failure recovery and reporting

## 🛠️ Troubleshooting

### Common Issues

#### 1. AWS Credentials Error
```
❌ AWS credentials not available: Unable to locate credentials
```
**Solution**: Configure AWS credentials
```bash
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-west-2
```

#### 2. Database Connection Error
```
❌ Failed to initialize memory manager: connection to server failed
```
**Solution**: Check PostgreSQL connection
```bash
# Ensure PostgreSQL is running
./docker-postgres.sh start

# Check .env file has correct database settings
cat .env | grep POSTGRES
```

#### 3. Import Error
```
❌ Import error: No module named 'mem0'
```
**Solution**: Install required packages
```bash
pip install mem0ai boto3 python-dotenv
```

#### 4. No Users Found
```
ℹ️  No users with memories found
```
**Solution**: Create some memories first
```bash
# Run the main agent to create memories
python langgraph_mem0_agent_enhanced.py
# Have some conversations, then try maintenance again
```

### Debug Mode
```bash
# Run with verbose output for debugging
./memory-maintenance --verbose --user your_user_id

# Check what would be done without making changes
./memory-maintenance --dry-run --all-users
```

## 🔗 Integration

### With Main Agent
The CLI tool uses the same memory manager as the main agent, ensuring consistency:

```python
# Both use the same Mem0MemoryManager
from mem0_memory_manager import Mem0MemoryManager
```

### With Monitoring Systems
```bash
# Export metrics for monitoring
./memory-maintenance --all-users --stats-only > memory-stats.json

# Check exit codes for automation
./memory-maintenance --user test_user
echo "Exit code: $?"
```

### With CI/CD Pipelines
```yaml
# GitHub Actions example
- name: Run Memory Maintenance
  run: |
    cd lg-m0-psql
    ./memory-maintenance --all-users --verbose
```

## 📈 Best Practices

1. **Regular Maintenance**: Run daily or weekly depending on usage
2. **Monitor Statistics**: Track memory health metrics over time
3. **Batch Processing**: Use `--all-users` for efficiency
4. **Dry Run First**: Test with `--dry-run` before production runs
5. **Log Output**: Redirect output to logs for monitoring
6. **Error Handling**: Check exit codes in automated scripts

The Memory Maintenance CLI provides a powerful, flexible way to manage your AI agent's memory system outside of the main application, perfect for scheduled maintenance, debugging, and system administration tasks.
