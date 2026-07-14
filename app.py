"""
Streamlit UI for Multi-Agent Research Paper Reviewer
"""
import streamlit as st
import sys
from pathlib import Path
import time
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agents.orchestration import get_orchestrator


def main():
    st.set_page_config(
        page_title="Research Paper Reviewer",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Multi-Agent Research Paper Reviewer")
    st.markdown("""
    A multi-agent system that assists in reviewing academic papers and summarizes them 
    for students to understand, learn, keep track, and follow.
    
    **Agents:**
    - 🔍 **Reader Agent**: Extracts paper content from Arxiv, PDFs, or URLs
    - ✍️ **MetaReviewer Agent**: Generates comprehensive reviews and student-friendly summaries
    - ✅ **Critic Agent**: Validates review quality and provides feedback
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        use_langgraph = st.checkbox("Use LangGraph (if available)", value=False)
        st.markdown("---")
        st.markdown("### 📊 System Info")
        
        try:
            from agents.llm_client import get_default_llm, CUDA_AVAILABLE, MPS_AVAILABLE
            llm = get_default_llm()
            backend_name = llm.backend.capitalize()
            model_name = llm.model
            gpu_support = "Enabled (CUDA)" if CUDA_AVAILABLE else ("Enabled (Apple Silicon MPS)" if MPS_AVAILABLE else "Disabled (CPU)")
        except Exception:
            backend_name = "Ollama"
            model_name = "llama3.2"
            gpu_support = "Enabled"
            
        st.info(f"""
        **LLM Backend:** {backend_name} ({model_name})
        
        **GPU Support:** {gpu_support}
        
        **Agents:** 3 (Reader, Reviewer, Critic)
        """)
    
    # Quick test from session state
    quick_test_value = None
    if 'quick_test' in st.session_state:
        quick_test_value = st.session_state.quick_test
        del st.session_state.quick_test
    
    # Main input section
    st.header("📥 Input")
    
    # Better input selection with descriptions
    input_type = st.radio(
        "Select input type:",
        ["Arxiv ID", "PDF Path", "URL"],
        horizontal=True,
        help="Choose how you want to provide the paper"
    )
    
    input_value = quick_test_value if quick_test_value else ""
    input_type_code = ""
    
    # Enhanced input fields with better descriptions
    if input_type == "Arxiv ID":
        st.info("💡 **Arxiv ID**: Enter the Arxiv paper identifier (e.g., 1706.03762 for 'Attention Is All You Need')")
        input_value = st.text_input(
            "Enter Arxiv Paper ID:",
            placeholder="e.g., 1706.03762",
            help="Format: YYMM.NNNNN (e.g., 1706.03762, 2301.12345)",
            key="arxiv_input"
        )
        input_type_code = "arxiv_id"
        if input_value and not input_value.replace('.', '').replace('-', '').isdigit():
            st.warning("⚠️ Arxiv IDs typically contain only numbers and dots (e.g., 1706.03762)")
        
    elif input_type == "PDF Path":
        st.info("💡 **PDF Path**: Provide the path to a local PDF file on your system")
        input_value = st.text_input(
            "Enter PDF file path:",
            placeholder="e.g., ./data/papers/paper.pdf or /path/to/paper.pdf",
            help="Enter the full or relative path to a PDF file",
            key="pdf_input"
        )
        input_type_code = "pdf_path"
        if input_value and not input_value.endswith('.pdf'):
            st.warning("⚠️ The file path should point to a PDF file (.pdf extension)")
        
    elif input_type == "URL":
        st.info("💡 **URL**: Enter a web URL pointing to a research paper")
        input_value = st.text_input(
            "Enter paper URL:",
            placeholder="e.g., https://arxiv.org/abs/1706.03762",
            help="Enter a valid URL to a research paper webpage",
            key="url_input"
        )
        input_type_code = "url"
        if input_value and not input_value.startswith(('http://', 'https://')):
            st.warning("⚠️ URL should start with http:// or https://")
    
    # Process button with better placement
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        process_button = st.button(
            "🚀 Review Paper", 
            type="primary", 
            use_container_width=True,
            help="Click to start the review process. This will use all 3 agents to analyze the paper."
        )
    
    # Show what will happen
    if input_value:
        st.markdown("### What will happen:")
        st.markdown("""
        1. **🔍 Reader Agent** will fetch and extract paper content
        2. **✍️ MetaReviewer Agent** will generate a comprehensive review and summary
        3. **✅ Critic Agent** will validate the review quality
        4. **📊 Results** will be displayed in organized tabs
        """)
    
    # Results section
    if process_button and input_value:
        if not input_value.strip():
            st.error("Please enter a valid input value.")
        else:
            # Initialize orchestrator
            try:
                with st.spinner("Initializing orchestrator..."):
                    orchestrator = get_orchestrator(use_langgraph=use_langgraph)
                
                # Process the paper with better progress tracking
                st.header("🔄 Processing")
                
                # Create placeholder for status
                status_container = st.container()
                with status_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    time_text = st.empty()
                
                start_time = time.time()
                
                # Step 1: Reader Agent
                with status_container:
                    status_text.markdown("**🔍 Reader Agent:** Fetching paper content from source...")
                    progress_bar.progress(15)
                    time_text.text(f"⏱️ Elapsed: {time.time() - start_time:.1f}s")
                
                # Run the full pipeline (this will call all agents)
                result = orchestrator.process(input_value, input_type=input_type_code)
                
                elapsed_time = time.time() - start_time
                
                # Update progress based on result
                with status_container:
                    if result.get('success'):
                        progress_bar.progress(100)
                        status_text.success(f"✅ **Complete!** All agents finished successfully")
                        time_text.text(f"⏱️ Total time: {elapsed_time:.2f}s")
                    else:
                        progress_bar.progress(50)
                        status_text.error("❌ **Processing failed** - Check errors below")
                        time_text.text(f"⏱️ Time before failure: {elapsed_time:.2f}s")
                
                # Display results
                st.header("📊 Results")
                
                if result.get('success'):
                    # Success message
                    st.success("✅ Paper review completed successfully!")
                    
                    # Create tabs for different result sections
                    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "📄 Review", "✅ Validation", "📈 Details"])
                    
                    with tab1:
                        st.subheader("Student-Friendly Summary")
                        summary = result.get('summary', 'No summary available.')
                        st.markdown(f"**Summary:**\n\n{summary}")
                        
                        # Summary metrics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Summary Length", f"{len(summary)} characters")
                        with col2:
                            sentences = [s.strip() for s in summary.split('.') if s.strip()]
                            st.metric("Number of Sentences", len(sentences))
                    
                    with tab2:
                        st.subheader("Comprehensive Review")
                        review = result.get('review', {})
                        
                        if isinstance(review, dict):
                            review_text = review.get('review_text', 'No review available.')
                            st.markdown(f"**Review:**\n\n{review_text}")
                            
                            # Review sections
                            if 'Main Contribution' in review_text:
                                st.markdown("### 📌 Review Sections Detected:")
                                sections = ['Main Contribution', 'Strengths', 'Weaknesses', 'Significance']
                                for section in sections:
                                    if section in review_text:
                                        st.markdown(f"- ✅ {section}")
                        else:
                            st.markdown(str(review))
                    
                    with tab3:
                        st.subheader("Review Validation")
                        validation = result.get('validation', {})
                        critic_output = result.get('critic', {})
                        
                        if critic_output:
                            validation = critic_output.get('validation', validation)
                            critique = critic_output.get('critique', '')
                            
                            # Validation status
                            is_complete = validation.get('is_complete', False)
                            if is_complete:
                                st.success("✅ Review is complete and validated")
                            else:
                                st.warning("⚠️ Review validation found some issues")
                            
                            # Validation metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                accuracy = validation.get('accuracy_score', 'N/A')
                                st.metric("Accuracy Score", f"{accuracy:.2f}" if isinstance(accuracy, (int, float)) else accuracy)
                            with col2:
                                clarity = validation.get('clarity_score', 'N/A')
                                st.metric("Clarity Score", f"{clarity:.2f}" if isinstance(clarity, (int, float)) else clarity)
                            
                            # Critique
                            if critique:
                                st.markdown("### 💬 Critique")
                                st.markdown(critique)
                            
                            # Validation text
                            validation_text = validation.get('validation_text', '')
                            if validation_text:
                                with st.expander("View Full Validation Details"):
                                    st.markdown(validation_text)
                        else:
                            st.info("Validation details not available.")
                    
                    with tab4:
                        st.subheader("Processing Details")
                        
                        # Agent statuses
                        st.markdown("### 🤖 Agent Status")
                        col1, col2, col3 = st.columns(3)
                        
                        reader = result.get('reader', {})
                        reviewer = result.get('reviewer', {})
                        critic = result.get('critic', {})
                        
                        with col1:
                            reader_status = reader.get('status', 'unknown')
                            if reader_status == 'success':
                                st.success("🔍 Reader: ✅")
                            else:
                                st.error(f"🔍 Reader: ❌")
                        
                        with col2:
                            reviewer_status = reviewer.get('status', 'unknown')
                            if reviewer_status == 'success':
                                st.success("✍️ Reviewer: ✅")
                            else:
                                st.error(f"✍️ Reviewer: ❌")
                        
                        with col3:
                            critic_status = critic.get('status', 'unknown')
                            if critic_status == 'success':
                                st.success("✅ Critic: ✅")
                            else:
                                st.error(f"✅ Critic: ❌")
                        
                        # Metadata
                        if reader and reader.get('metadata'):
                            st.markdown("### 📋 Paper Metadata")
                            metadata = reader.get('metadata', {})
                            metadata_col1, metadata_col2 = st.columns(2)
                            
                            with metadata_col1:
                                st.markdown(f"**Title:** {metadata.get('title', 'N/A')}")
                                st.markdown(f"**Authors:** {', '.join(metadata.get('authors', []))}")
                            
                            with metadata_col2:
                                st.markdown(f"**Published:** {metadata.get('published', 'N/A')}")
                                if metadata.get('pdf_url'):
                                    st.markdown(f"**PDF URL:** [Link]({metadata['pdf_url']})")
                        
                        # Performance metrics
                        st.markdown("### ⏱️ Performance Metrics")
                        perf_col1, perf_col2, perf_col3 = st.columns(3)
                        with perf_col1:
                            st.metric("Total Time", f"{elapsed_time:.2f}s")
                        with perf_col2:
                            tool_calls = sum([
                                1 if reader.get('status') == 'success' else 0,
                                1 if reviewer.get('status') == 'success' else 0,
                                1 if critic.get('status') == 'success' else 0
                            ])
                            st.metric("Tool Calls", tool_calls)
                        with perf_col3:
                            st.metric("Agents Used", "3")
                        
                        # Raw JSON (expandable)
                        with st.expander("View Raw JSON Output"):
                            st.json(result)
                
                else:
                    # Error handling
                    st.error("❌ Failed to process paper review.")
                    errors = result.get('errors', [])
                    if errors:
                        st.markdown("### Errors:")
                        for error in errors:
                            st.error(f"- {error}")
                    
                    # Show partial results if available
                    if result.get('reader'):
                        st.warning("Partial results may be available. Check the Details tab.")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    # Enhanced example section
    with st.expander("📚 Example Usage & Quick Test", expanded=False):
        st.markdown("""
        **Quick Test Examples:**
        
        1. **Transformer Paper (Arxiv ID):** 
           - Enter: `1706.03762`
           - This is the famous "Attention Is All You Need" paper
           - ✅ Recommended for first test
        
        2. **Other Arxiv Papers:** 
           - Format: `YYMM.NNNNN` (e.g., `2301.12345`, `2012.12345`)
           - Find papers at: https://arxiv.org
        
        3. **Local PDF:** 
           - Path: `./data/papers/paper.pdf` or `/full/path/to/paper.pdf`
           - Make sure the file exists and is readable
        
        4. **URL:** 
           - Example: `https://arxiv.org/abs/1706.03762`
           - Any URL pointing to a research paper
        
        **💡 Tips:**
        - Start with Arxiv ID `1706.03762` for a quick test
        - Processing takes 10-30 seconds depending on paper size
        - Results are displayed in organized tabs below
        - Check the "Details" tab for full metrics and metadata
        
        **⚙️ System Info:**
        - LLM: GPT-2 (HuggingFace Local, GPU-accelerated)
        - For better quality, consider using Ollama with llama3.2
        """)
        
        # Quick test button
        if st.button("🚀 Quick Test with Transformer Paper", use_container_width=True):
            st.session_state.quick_test = "1706.03762"
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Multi-Agent Research Paper Reviewer | Built with Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

