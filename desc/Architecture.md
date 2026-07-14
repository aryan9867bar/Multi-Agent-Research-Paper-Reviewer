# Architecture Documentation

## Agent Roles

### 1. Reader Agent
**Role**: Extract and parse paper content

**Responsibilities**:
- Fetch papers from Arxiv by ID
- Download and extract PDF content
- Parse web-based paper sources
- Extract structured information (topic, contributions, methodology, results)
- Provide clean, structured output for downstream agents

**Tools Used**:
- `ArxivAPITool`: Search and fetch papers
- `PDFExtractorTool`: Extract text from PDFs
- `WebCrawlerTool`: Fetch web content
- `FileIOTool`: Save/load paper data

**Input**: Paper ID, PDF path, or URL
**Output**: Structured paper content with metadata

### 2. MetaReviewer Agent
**Role**: Generate comprehensive reviews and student-friendly summaries

**Responsibilities**:
- Analyze paper content
- Generate detailed reviews (strengths, weaknesses, novelty, clarity, significance)
- Create student-friendly summaries
- Identify key learnings and takeaways
- Save reviews for future reference

**Tools Used**:
- `FileIOTool`: Save reviews to disk
- LLM: Generate reviews and summaries

**Input**: Paper content from Reader Agent
**Output**: Review and summary

### 3. Critic Agent
**Role**: Validate review quality and provide feedback

**Responsibilities**:
- Validate review completeness
- Check review accuracy against original paper
- Assess clarity and structure
- Provide constructive critique
- Suggest improvements if needed

**Tools Used**:
- `FileIOTool`: Access review files
- LLM: Generate critiques and validations

**Input**: Review from MetaReviewer Agent + Original paper content
**Output**: Validation results and critique

## Message Schema

### Agent State (Orchestration)

```python
{
    "input": str,              # Original input (paper ID, PDF path, URL)
    "input_type": str,         # 'arxiv_id', 'pdf_path', or 'url'
    "reader_output": {
        "agent": "Reader",
        "status": "success" | "error",
        "content": str,
        "metadata": dict,
        "structured_info": dict
    },
    "reviewer_output": {
        "agent": "MetaReviewer",
        "status": "success" | "error",
        "review": dict,
        "summary": str
    },
    "critic_output": {
        "agent": "Critic",
        "status": "success" | "error",
        "validation": dict,
        "critique": str,
        "improved_review": dict | None
    },
    "final_output": {
        "input": str,
        "input_type": str,
        "success": bool,
        "summary": str,
        "review": dict,
        "validation": dict,
        "critique": str,
        "errors": list
    },
    "errors": list[str]
}
```

### MCP Request Schema

```json
{
    "method": "tools/list" | "tools/call",
    "params": {
        "name": "tool_name",
        "arguments": {
            "arg1": "value1",
            "arg2": "value2"
        }
    }
}
```

### MCP Response Schema

```json
{
    "content": [
        {
            "type": "text",
            "text": "response content"
        }
    ],
    "error": "error message (if any)"
}
```

## Communication Flow

### Sequential Flow (Simple Orchestrator)

```
Input → Reader Agent → Reviewer Agent → Critic Agent → Final Output
         ↓                ↓                ↓
      Tools Used      Tools Used      Tools Used
```

### Graph Flow (LangGraph)

```
[Entry] → [Reader Node] → [Reviewer Node] → [Critic Node] → [Finalize Node] → [End]
            ↓                  ↓                 ↓
         Tools             Tools            Tools
```

### MCP Flow

```
MCP Client → Reader Server → Reviewer Server → Critic Server
              (port 8001)      (port 8002)      (port 8003)
```

## Tool Contracts

### ArxivAPITool

**search_papers(query: str, max_results: int) -> List[Dict]**
- Returns list of paper metadata

**get_paper_by_id(paper_id: str) -> Dict**
- Returns paper metadata and abstract

**download_pdf(pdf_url: str, save_path: str) -> bool**
- Downloads PDF to specified path

### PDFExtractorTool

**extract_text(pdf_path: str) -> str**
- Returns extracted text from PDF

**extract_metadata(pdf_path: str) -> Dict**
- Returns PDF metadata (title, author, pages, etc.)

### FileIOTool

**read_file(filepath: str) -> str**
- Reads file content

**write_file(filepath: str, content: str) -> bool**
- Writes content to file

**list_files(directory: str) -> List[str]**
- Lists files in directory

### WebCrawlerTool

**fetch_url(url: str) -> str**
- Fetches and extracts text from URL

## Assumptions

1. **LLM Availability**: Assumes LLM is available (Ollama running locally or API accessible)
2. **Internet Connection**: Required for Arxiv API access
3. **PDF Format**: Assumes PDFs are text-based (not scanned images)
4. **Arxiv IDs**: Assumes valid Arxiv paper IDs (format: YYMM.NNNNN)
5. **File System**: Assumes write permissions in `./data/` directory
6. **MCP Servers**: Assumes servers are running if using MCP client
7. **Tool Reliability**: Assumes tools handle errors gracefully

## Error Handling

- Each agent catches exceptions and returns error status
- Orchestrator continues with partial results if one agent fails
- MCP servers return error responses for invalid requests
- Evaluation harness tracks errors and constraint violations

## Scalability Considerations

- Agents can be deployed as separate services
- MCP servers can run on different machines
- LLM calls can be batched or cached
- Paper downloads can be cached to avoid re-downloading
- Reviews can be stored in database for faster retrieval

