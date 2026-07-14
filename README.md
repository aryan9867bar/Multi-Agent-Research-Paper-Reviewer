# Multi-Agent Research Paper Reviewer

## Overview

A multi-agent system that assists in reviewing academic papers and summarizes them for students to understand, learn, keep track, and follow. The system uses three specialized agents working together to provide comprehensive paper reviews.

## Architecture

![Architecture Diagram](Architecture_Diagram.png)

### Agents

1. **Reader Agent**: Reads and extracts content from research papers
   - Fetches papers from Arxiv
   - Extracts text from PDFs
   - Parses web content
   - Extracts structured information

2. **MetaReviewer Agent**: Reviews and summarizes papers
   - Generates comprehensive reviews
   - Creates student-friendly summaries
   - Identifies key contributions and findings

3. **Critic Agent**: Validates review quality
   - Validates review completeness
   - Provides constructive critique
   - Suggests improvements

### Tools

Each agent uses specialized tools:
- **File I/O**: Read/write files, list directories
- **Arxiv API**: Search and fetch papers from Arxiv
- **PDF Extractor**: Extract text and metadata from PDFs
- **Web Crawler**: Fetch content from URLs

### MCP (Model Context Protocol) Implementation

Each agent is deployed as an MCP server:
- `reader-server` (port 8001)
- `reviewer-server` (port 8002)
- `critic-server` (port 8003)

## Project Structure

```
part2_multi_agent/
├── agents/
│   ├── __init__.py
│   ├── reader_agent.py          # Reader agent
│   ├── meta_reviewer_agent.py   # Reviewer agent
│   ├── critic_agent.py          # Critic agent
│   ├── orchestration.py         # Multi-agent orchestration
│   ├── tools.py                 # Shared tools
│   └── llm_client.py            # LLM client (Ollama/OpenAI/HuggingFace)
├── mcp-server/
│   ├── __init__.py
│   ├── server_base.py           # Base MCP server
│   ├── reader_server.py         # Reader MCP server
│   ├── reviewer_server.py       # Reviewer MCP server
│   ├── critic_server.py         # Critic MCP server
│   └── client.py                # MCP client
├── eval/
│   ├── test_cases.json          # Test cases
│   └── run_eval.py              # Evaluation harness
├── data/                        # Data directory (created at runtime)
│   ├── papers/                  # Downloaded papers
│   └── reviews/                 # Generated reviews
├── requirements.txt
├── README.md
└── ARCH.md
```

## Quick Start

### 1. Install Dependencies

```bash
cd Multi-Agent-Research-Paper-Reviewer
pip install -r requirements.txt
```

### 2. Setup LLM (Ollama - Recommended)

Install Ollama: https://ollama.ai

```bash
# Pull a model (free, runs locally)
ollama pull llama3.2
```

Or use OpenAI/HuggingFace (requires API keys).

### 3. Run Orchestrator

```bash
cd agents
python orchestration.py
```

### 4. Run Evaluation

```bash
cd eval
python run_eval.py
```

### 5. Run Interactive UI (Optional)

```bash
# Install streamlit if not already installed
pip install streamlit

# Run the UI
streamlit run app.py
```

The UI will open in your browser at `http://localhost:8501`. You can:
- Enter Arxiv paper IDs, PDF paths, or URLs
- View real-time processing status
- See comprehensive reviews, summaries, and validation results
- Explore detailed metrics and agent status

### 6. Deploy to Streamlit Cloud (Share Your App)

To deploy and share your app with a public link:

**Option A: Streamlit Cloud (Free, Recommended)**
```bash
# 1. Push your code to GitHub
git init  # if not already a git repo
git add .
git commit -m "Deploy multi-agent paper reviewer"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main

# 2. Go to https://streamlit.io/cloud
# 3. Click "New app"
# 4. Select your repository
# 5. Set main file path to: app.py
# 6. Click "Deploy"
```

Your app will be live at: `https://<your-app-name>.streamlit.app`

**Option B: Self-Hosted with ngrok (For GPU Access)**
```bash
# Run Streamlit
streamlit run app.py --server.port=8501

# In another terminal, create ngrok tunnel
ngrok http 8501

# Share the ngrok URL (e.g., https://abc123.ngrok.io)
```

**Note**: Streamlit Cloud has no GPU support. For GPU access, use Option B or deploy on your own server.

See `STREAMLIT_CLOUD_SETUP.md` for detailed deployment instructions.

## Usage

### Using the Orchestrator

```python
from agents.orchestration import get_orchestrator

orchestrator = get_orchestrator(use_langgraph=False)

# Review a paper by Arxiv ID
result = orchestrator.process("1706.03762", input_type="arxiv_id")

if result['success']:
    print(result['summary'])
    print(result['review'])
else:
    print(f"Errors: {result['errors']}")
```

### Using MCP Servers

Start servers (in separate terminals):

```bash
# Terminal 1
python mcp-server/reader_server.py

# Terminal 2
python mcp-server/reviewer_server.py

# Terminal 3
python mcp-server/critic_server.py
```

Then use the client:

```python
from mcp_server.client import MCPClient

client = MCPClient()
result = client.review_paper("1706.03762", input_type="arxiv_id")
```

## Evaluation

The evaluation harness includes 6+ test cases covering:
- Paper review functionality
- Error handling
- Review quality validation
- Multi-agent coordination
- Structured information extraction

Run evaluation:

```bash
cd eval
python run_eval.py
```

Metrics computed:
- Success rate
- Constraint violations
- Latency
- Tool call count

## Configuration

### GPU Support

**The system automatically uses GPUs if available!**

- **4x Tesla V100 GPUs detected** - All GPUs will be utilized
- **Automatic GPU detection** - No configuration needed
- **Multi-GPU distribution** - Large models automatically distributed across GPUs
- **FP16 precision** - Optimized for speed and memory

See `GPU_CONFIGURATION.md` for detailed GPU usage information.

### LLM Backend

The system supports multiple backends with GPU acceleration:

**Option 1: HuggingFace Local (Recommended for GPU)**
- Uses local models with GPU acceleration
- Automatically distributes across all available GPUs
- Best performance on local hardware
- Default if CUDA is available

**Option 2: Ollama (Also GPU-Accelerated)**
- Automatically uses GPU if CUDA available
- Free and local
- Good for testing

**Option 3: OpenAI/HuggingFace API**
- Cloud-based (no local GPU)
- Requires API keys

Edit `agents/llm_client.py` or set environment variables:

```bash
# For Ollama (uses GPU automatically)
export OLLAMA_BASE_URL=http://localhost:11434

# For OpenAI (cloud, no GPU)
export OPENAI_API_KEY=your_key_here

# For HuggingFace API (cloud, no GPU)
export HUGGINGFACE_API_KEY=your_key_here
```

### MCP Server Ports

Default ports:
- Reader: 8001
- Reviewer: 8002
- Critic: 8003

Modify in server files if needed.

## Data Sources

- **Arxiv API**: Free, no API key required
- **Arxiv Metadata**: Available on Kaggle
- **Arxiv Abstracts**: Available on HuggingFace

## Features

- ✅ Multi-agent orchestration (LangGraph or simple sequential)
- ✅ MCP protocol implementation
- ✅ Comprehensive tool usage
- ✅ Error handling and validation
- ✅ Evaluation harness with metrics
- ✅ **GPU acceleration** - Automatically uses all available GPUs
- ✅ Multi-GPU support - Distributes models across multiple GPUs
- ✅ Free and open-source (uses Ollama or HuggingFace local models)

## Limitations

- PDF extraction quality depends on PDF format
- LLM responses may vary (use temperature settings)
- Arxiv API has rate limits
- Requires internet connection for Arxiv access

## Future Improvements

- Add more agents (e.g., CitationAgent)
- Improve PDF extraction
- Add caching for papers
- Support for more paper sources

