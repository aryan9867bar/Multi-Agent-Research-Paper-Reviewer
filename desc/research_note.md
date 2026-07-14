# Research Note: Multi-Agent Research Paper Reviewer

## Setup

### Environment
- Python 3.8+
- Ollama (local LLM) or OpenAI/HuggingFace API
- Internet connection for Arxiv API

### Installation
```bash
pip install -r requirements.txt
ollama pull llama3.2  # For local LLM
```

### Configuration
- Default LLM: Ollama with llama3.2 (free, local)
- MCP servers: Ports 8001-8003
- Data directory: `./data/`

## System Architecture

The system implements a three-agent architecture:

1. **Reader Agent**: Extracts paper content using Arxiv API, PDF extraction, and web crawling
2. **MetaReviewer Agent**: Generates reviews and student-friendly summaries using LLM
3. **Critic Agent**: Validates review quality and provides feedback

Agents communicate through a shared state in the orchestrator, with each agent using specialized tools for their tasks.

## Metrics

### Evaluation Results

Based on 6 test cases covering:
- Paper review functionality
- Error handling
- Review quality validation
- Multi-agent coordination
- Structured information extraction

**Key Metrics**:
- Success Rate: ~83% (5/6 tests passing)
- Average Latency: ~15-30 seconds per paper review
- Tool Calls: ~3 per review (one per agent)
- Constraint Violations: Minimal (mostly edge cases)

### Performance Characteristics

- **Latency**: Dominated by LLM inference time (10-20s) and Arxiv API calls (2-5s)
- **Accuracy**: High for well-structured papers, lower for scanned PDFs
- **Reliability**: Good error handling, graceful degradation on failures

## Key Insights

### 1. Agent Specialization Works Well

Each agent's focused role (reading, reviewing, critiquing) leads to:
- Clear separation of concerns
- Easier debugging and improvement
- Better tool utilization

### 2. Tool Integration is Critical

The system's effectiveness depends heavily on:
- Arxiv API reliability (free, no rate limits for reasonable use)
- PDF extraction quality (varies by PDF format)
- LLM response quality (better with larger models)

### 3. Error Handling is Essential

Real-world scenarios include:
- Invalid paper IDs
- Network failures
- Malformed PDFs
- LLM timeouts

Robust error handling ensures the system degrades gracefully.

### 4. MCP Protocol Enables Flexibility

MCP servers allow:
- Independent agent deployment
- Easy integration with other systems
- Scalable architecture

### 5. Student-Friendly Summaries Require Careful Prompting

The MetaReviewer agent uses specific prompts to:
- Simplify technical language
- Highlight key learnings
- Provide context for students

This requires careful prompt engineering.

## Figures

### Figure 1: System Architecture

```
┌─────────────┐
│   Input     │ (Paper ID/PDF/URL)
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────┐
│   Reader    │────▶│  Tools   │ (Arxiv, PDF, Web)
│   Agent     │     └──────────┘
└──────┬──────┘
       │ Paper Content
       ▼
┌─────────────┐     ┌──────────┐
│  Reviewer   │────▶│  Tools   │ (File I/O, LLM)
│   Agent     │     └──────────┘
└──────┬──────┘
       │ Review + Summary
       ▼
┌─────────────┐     ┌──────────┐
│   Critic    │────▶│  Tools   │ (File I/O, LLM)
│   Agent     │     └──────────┘
└──────┬──────┘
       │ Validation + Critique
       ▼
┌─────────────┐
│Final Output │ (Summary, Review, Validation)
└─────────────┘
```

### Figure 2: Evaluation Metrics

**Success Rate by Test Case**:
- Test 001 (Transformer Paper): ✓ PASS
- Test 002 (Search and Review): ✓ PASS
- Test 003 (Invalid ID): ✓ PASS (error handling)
- Test 004 (Quality Check): ✓ PASS
- Test 005 (Multi-Agent): ✓ PASS
- Test 006 (Structured Info): ⚠ PARTIAL (depends on LLM)

**Average Latency Breakdown**:
- Reader Agent: 5-10s (Arxiv API + PDF extraction)
- Reviewer Agent: 10-15s (LLM generation)
- Critic Agent: 5-10s (LLM validation)
- Total: 20-35s per paper

## Challenges and Solutions

### Challenge 1: PDF Extraction Quality
**Problem**: Some PDFs are scanned images or have complex layouts
**Solution**: Use pdfplumber (better than PyPDF2) and fallback to metadata extraction

### Challenge 2: LLM Response Consistency
**Problem**: LLM responses vary in format and quality
**Solution**: Structured prompts, temperature tuning, and post-processing

### Challenge 3: Error Propagation
**Problem**: One agent failure breaks entire pipeline
**Solution**: Error handling at each step, partial results, and error reporting

### Challenge 4: Latency
**Problem**: Sequential processing is slow
**Solution**: Could parallelize independent operations, cache results

## Interactive UI

A Streamlit-based web interface has been implemented to provide an easy-to-use interface for the multi-agent system. The UI allows users to:

- **Input Methods**: Enter papers via Arxiv ID, PDF path, or URL
- **Real-time Processing**: View progress as agents process the paper
- **Comprehensive Results**: Display summaries, reviews, and validation in organized tabs
- **Metrics Dashboard**: View performance metrics, agent status, and paper metadata
- **Error Handling**: Clear error messages and partial result display

To run the UI:
```bash
streamlit run app.py
```

The UI demonstrates the end-to-end flow of the multi-agent system and makes it accessible to non-technical users.

## Future Work

1. **Add More Agents**: CitationAgent, RelatedPapersAgent
2. **Improve PDF Handling**: OCR for scanned PDFs, better layout analysis
3. **Caching**: Cache paper downloads and reviews
4. **Batch Processing**: Review multiple papers at once
5. **Database Integration**: Store reviews in database for faster retrieval
6. **Fine-tuning**: Fine-tune LLM on academic paper reviews

## Conclusion

The multi-agent system successfully demonstrates:
- Effective agent specialization
- Tool integration and usage
- MCP protocol implementation
- Robust error handling
- Practical utility for students

The system provides a solid foundation for academic paper review assistance, with clear paths for improvement and extension.

