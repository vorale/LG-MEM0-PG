# 🧠 Memory Dashboard Setup Guide

A simple web dashboard to visualize and explore the memory state of your LangGraph + Mem0 AI Agent for any user ID.

## 🎯 Dashboard Overview

The Memory Dashboard provides a comprehensive view of your AI agent's memory system, allowing you to:
- **Monitor memory state** for specific users
- **Visualize memory patterns** and categories
- **Search and filter** stored memories
- **Track memory creation** over time
- **Understand memory distribution** across different topics

## 📊 Dashboard Features

### **Overview Metrics Panel**
- **Total Memories**: Count of all memories for the user
- **Recent Memories**: Memories created in the last 24 hours  
- **Categories**: Auto-categorized memory types
- **Average Length**: Average character length of memories

### **🏷️ Automatic Memory Categorization**
The dashboard automatically categorizes memories into:
- 🎯 **Preferences** (likes, dislikes, favorites)
- 💼 **Professional** (work, career, projects)
- 👥 **Personal** (family, friends, relationships)
- 🎨 **Interests** (hobbies, sports, entertainment)
- ✈️ **Travel** (trips, vacations, places)
- 📝 **General** (everything else)

### **📈 Interactive Visualizations**
- **Pie Chart**: Memory distribution by category
- **Timeline Scatter Plot**: When memories were created over time
- **Detailed Memory List**: Expandable cards with full memory content

### **🔍 Interactive Features**
- **User ID Input**: Switch between different users
- **Real-time Search**: Find memories by keywords
- **Category Filter**: Filter memories by auto-assigned categories
- **Refresh Data**: Reload memories from database
- **Raw Data View**: JSON view of complete memory data

## 🛠️ Installation & Setup

### **Prerequisites**
- Your LangGraph + Mem0 AI Agent project is already set up
- PostgreSQL database is running (local Docker or Aurora)
- Python environment with existing project dependencies

### **Step 1: Install Dashboard Dependencies**

```bash
# Install required packages for the dashboard
pip install -r requirements-dashboard.txt
```

Or install manually:
```bash
pip install streamlit>=1.28.0 plotly>=5.15.0 pandas>=2.0.0
```

### **Step 2: Verify Environment Configuration**

Make sure your `.env` file contains the database configuration:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database
AWS_DEFAULT_REGION=us-west-2
```

### **Step 3: Start Your Database**

For local development:
```bash
./docker-postgres.sh start
```

For Aurora Serverless:
```bash
./switch-env.sh aurora
```

## 🚀 Running the Dashboard

### **Method 1: Using the Run Script (Recommended)**
```bash
./run-dashboard.sh
```

### **Method 2: Manual Launch**
```bash
streamlit run memory_dashboard.py --server.port 8501 --server.address localhost
```

### **Method 3: Custom Configuration**
```bash
# Run on different port
streamlit run memory_dashboard.py --server.port 8502

# Run with specific config
streamlit run memory_dashboard.py --server.headless true
```

## 🌐 Accessing the Dashboard

1. **Open your browser** to: `http://localhost:8501`
2. **Enter a User ID** in the sidebar (e.g., "default_user")
3. **Click "Refresh Data"** to load memories
4. **Explore the visualizations** and memory details

## 📋 Dashboard Layout & Navigation

```
🧠 AI Agent Memory Dashboard
├── 🔧 Sidebar Controls
│   ├── 👤 User ID Input Field
│   ├── 🔄 Refresh Data Button
│   └── 📊 Dashboard Info Panel
│
├── 📈 Overview Metrics (Top Row)
│   ├── 🧠 Total Memories
│   ├── 🕐 Recent (24h)
│   ├── 🏷️ Categories
│   └── 📏 Average Length
│
├── 🏷️ Memory Categories Section
│   └── 📊 Interactive Pie Chart
│
├── 📅 Memory Timeline Section
│   └── 📈 Scatter Plot with Hover Details
│
└── 📋 Detailed Memory List
    ├── 🔍 Search Input
    ├── 🏷️ Category Filter
    └── 📝 Expandable Memory Cards
        ├── 💭 Memory Content
        ├── 📊 Metadata & Details
        ├── 🆔 Memory ID
        ├── 📅 Timestamps
        └── ⭐ Relevance Score
```

## 🎨 Understanding the Display

### **Memory Cards Show:**
- **Memory Content**: The actual stored memory text
- **Category**: Auto-assigned category with emoji icon
- **Creation Time**: When the memory was first stored
- **Update Time**: When the memory was last modified
- **Memory ID**: Unique identifier for the memory
- **Metadata**: Additional structured data (if any)
- **Relevance Score**: Similarity score (if from search results)

### **Color Coding:**
- **Categories**: Each category has a distinct color in charts
- **Timeline**: Points colored by category for easy identification
- **Status Indicators**: Green for recent, blue for older memories

## 🔧 Usage Examples

### **Monitoring User Interactions**
1. Run your AI agent and have conversations
2. Switch to the dashboard and enter the user ID
3. See new memories appear in real-time (after refresh)
4. Track how memories are categorized and stored

### **Debugging Memory Issues**
1. Search for specific keywords in memories
2. Check if expected memories are being stored
3. Verify memory categories are correct
4. Examine raw JSON data for troubleshooting

### **Understanding Memory Patterns**
1. Use the timeline to see memory creation patterns
2. Check category distribution to understand user topics
3. Monitor memory growth over time
4. Identify most active conversation periods

## 🚨 Troubleshooting

### **Common Issues**

**1. "No memories found" Message**
- Verify the user ID is correct
- Ensure the AI agent has been used to create memories
- Check database connection in `.env` file
- Confirm PostgreSQL is running

**2. "Failed to initialize Mem0" Error**
- Check AWS credentials are configured
- Verify Bedrock access permissions
- Ensure PostgreSQL connection parameters are correct
- Check if pgvector extension is installed

**3. Dashboard Won't Load**
- Ensure Streamlit is installed: `pip install streamlit`
- Check if port 8501 is available
- Try running on a different port: `streamlit run memory_dashboard.py --server.port 8502`

**4. Empty Visualizations**
- Verify memories exist for the specified user ID
- Check if timestamps are in correct format
- Ensure memory content is not empty

### **Debug Mode**
Enable detailed logging by adding to the top of `memory_dashboard.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### **Database Connection Test**
Test your database connection:
```bash
python setup_postgres.py
```

## 🔄 Workflow Integration

### **Development Workflow**
1. **Start Database**: `./docker-postgres.sh start`
2. **Run AI Agent**: `./run-agent.sh`
3. **Have Conversations**: Create some memories
4. **Launch Dashboard**: `./run-dashboard.sh`
5. **Monitor Memories**: View and analyze stored data

### **Production Monitoring**
1. **Deploy Dashboard**: Run on server with Aurora connection
2. **Set Up Monitoring**: Track memory growth and patterns
3. **Regular Reviews**: Check memory quality and relevance
4. **Performance Analysis**: Monitor memory retrieval patterns

## 📁 Dashboard Files

| File | Purpose | Description |
|------|---------|-------------|
| `memory_dashboard.py` | Main dashboard | Streamlit application with all visualizations |
| `run-dashboard.sh` | Launch script | Automated dashboard startup with dependency checks |
| `requirements-dashboard.txt` | Dependencies | Additional packages needed for dashboard |
| `MEMORY_DASHBOARD.md` | Documentation | This setup guide |

## 🎯 Next Steps

### **Basic Usage**
1. Follow the installation steps above
2. Run the dashboard and explore your memories
3. Try different user IDs to see different memory sets
4. Use search and filtering to find specific memories

### **Advanced Exploration**
1. Monitor memory patterns over time
2. Analyze category distributions for insights
3. Use the raw JSON view for detailed debugging
4. Track memory creation patterns during conversations

### **Customization Ideas**
- Modify category rules in `categorize_memory()` function
- Add new visualization types (word clouds, network graphs)
- Implement memory export functionality
- Add memory editing capabilities
- Create memory comparison between users

## 🆘 Support

If you encounter issues:

1. **Check Prerequisites**: Ensure your main AI agent works first
2. **Verify Database**: Run `python setup_postgres.py`
3. **Test Connection**: Check `.env` configuration
4. **Review Logs**: Look for error messages in terminal
5. **Restart Services**: Try restarting PostgreSQL and dashboard

For additional help, refer to the main project documentation in `README.md`.

---

**Happy Memory Exploring! 🧠✨**
