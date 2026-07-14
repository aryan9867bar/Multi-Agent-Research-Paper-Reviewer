"""
LLM Client - supports multiple backends (Ollama, OpenAI, HuggingFace)
GPU-accelerated for local models
"""
import os
from typing import Optional, List, Dict
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import GPU-related libraries
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    MPS_AVAILABLE = torch.backends.mps.is_available()
    DEVICE = "cuda" if CUDA_AVAILABLE else ("mps" if MPS_AVAILABLE else "cpu")
    if CUDA_AVAILABLE:
        DEVICE_COUNT = torch.cuda.device_count()
    elif MPS_AVAILABLE:
        DEVICE_COUNT = 1
    else:
        DEVICE_COUNT = 0
except ImportError:
    CUDA_AVAILABLE = False
    MPS_AVAILABLE = False
    DEVICE = "cpu"
    DEVICE_COUNT = 0

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class LLMClient:
    """Unified LLM client supporting multiple backends with GPU acceleration"""
    
    def __init__(self, backend: str = "huggingface_local", model: str = "microsoft/DialoGPT-medium", 
                 base_url: Optional[str] = None, api_key: Optional[str] = None,
                 use_gpu: bool = True, device: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            backend: "ollama", "openai", "huggingface" (API), or "huggingface_local" (GPU)
            model: Model name
            base_url: Base URL for API (for Ollama, defaults to http://localhost:11434)
            api_key: API key (for OpenAI/HuggingFace API)
            use_gpu: Whether to use GPU if available (for local models)
            device: Specific device to use ("cuda", "cuda:0", "cpu", etc.)
        """
        self.backend = backend.lower()
        self.model = model
        self.use_gpu = use_gpu and CUDA_AVAILABLE
        self.device = device or (DEVICE if self.use_gpu else "cpu")
        
        # Initialize model if using local HuggingFace
        self.local_model = None
        self.local_tokenizer = None
        self.local_pipeline = None
        
        if self.backend == "ollama":
            self.base_url = base_url or "http://localhost:11434"
            # Ollama automatically uses GPU if available, but we can verify
            if self.use_gpu:
                print(f"✓ Using Ollama with GPU support (CUDA available: {CUDA_AVAILABLE})")
        elif self.backend == "openai":
            self.base_url = base_url or "https://api.openai.com/v1"
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            print("⚠️  OpenAI API uses cloud servers (no local GPU)")
        elif self.backend == "huggingface":
            self.base_url = base_url or "https://router.huggingface.co/hf-inference"
            self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
            print("⚠️  HuggingFace API uses cloud servers (no local GPU)")
        elif self.backend == "huggingface_local":
            if not TRANSFORMERS_AVAILABLE:
                raise ImportError("transformers library required for local HuggingFace models. Install with: pip install transformers accelerate")
            self._load_local_model()
        else:
            raise ValueError(f"Unsupported backend: {backend}. Use 'ollama', 'openai', 'huggingface', or 'huggingface_local'")
    
    def _load_local_model(self):
        """Load HuggingFace model locally with GPU support"""
        try:
            print(f"Loading model '{self.model}' on device: {self.device}")
            if self.use_gpu:
                print(f"✓ GPU acceleration enabled ({DEVICE_COUNT} GPU(s) available)")
            
            # Load tokenizer
            self.local_tokenizer = AutoTokenizer.from_pretrained(self.model)
            if self.local_tokenizer.pad_token is None:
                self.local_tokenizer.pad_token = self.local_tokenizer.eos_token
            
            # Load model with GPU support
            model_kwargs = {}
            if self.use_gpu:
                model_kwargs["device_map"] = "auto"  # Automatically distribute across GPUs
                model_kwargs["dtype"] = torch.float16  # Use half precision for speed
            
            self.local_model = AutoModelForCausalLM.from_pretrained(
                self.model,
                **model_kwargs
            )
            
            # Create pipeline for easier generation
            # If device_map="auto" was used, don't specify device in pipeline
            pipeline_kwargs = {
                "model": self.local_model,
                "tokenizer": self.local_tokenizer,
            }
            
            # Only set device if not using device_map="auto"
            if self.use_gpu and "device_map" not in model_kwargs:
                pipeline_kwargs["device"] = 0
                pipeline_kwargs["dtype"] = torch.float16
            elif not self.use_gpu:
                pipeline_kwargs["device"] = -1
                pipeline_kwargs["dtype"] = torch.float32
            else:
                # Using device_map="auto", don't set device
                pipeline_kwargs["dtype"] = torch.float16 if self.use_gpu else torch.float32
            
            self.local_pipeline = pipeline("text-generation", **pipeline_kwargs)
            
            print(f"✓ Model loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading local model: {e}")
            print("Falling back to CPU or API-based backend")
            raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text from prompt"""
        if self.backend == "ollama":
            return self._generate_ollama(prompt, system_prompt, temperature, max_tokens)
        elif self.backend == "openai":
            return self._generate_openai(prompt, system_prompt, temperature, max_tokens)
        elif self.backend == "huggingface":
            return self._generate_huggingface(prompt, system_prompt, temperature, max_tokens)
        elif self.backend == "huggingface_local":
            return self._generate_huggingface_local(prompt, system_prompt, temperature, max_tokens)
    
    def _generate_ollama(self, prompt: str, system_prompt: Optional[str],
                        temperature: float, max_tokens: int) -> str:
        """Generate using Ollama (automatically uses GPU if available)"""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt or "You are a helpful AI assistant.",
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Ollama automatically uses GPU if CUDA is available
            # No explicit GPU flag needed - it detects CUDA automatically
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _generate_openai(self, prompt: str, system_prompt: Optional[str],
                        temperature: float, max_tokens: int) -> str:
        """Generate using OpenAI API"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _generate_huggingface(self, prompt: str, system_prompt: Optional[str],
                             temperature: float, max_tokens: int) -> str:
        """Generate using HuggingFace API"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"{self.base_url}/models/{self.model}"
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            elif isinstance(result, dict):
                return result.get("generated_text", str(result))
            else:
                return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _generate_huggingface_local(self, prompt: str, system_prompt: Optional[str],
                                   temperature: float, max_tokens: int) -> str:
        """Generate using local HuggingFace model with GPU"""
        try:
            if self.local_pipeline is None:
                return "Error: Local model not loaded"
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Truncate prompt if too long (most models have 1024 token limit)
            # Tokenize to check length
            tokens = self.local_tokenizer.encode(full_prompt)
            max_input_length = 512  # Leave room for generation
            if len(tokens) > max_input_length:
                # Truncate from the beginning, keep the end (more relevant)
                tokens = tokens[-max_input_length:]
                full_prompt = self.local_tokenizer.decode(tokens, skip_special_tokens=True)
            
            # Generate with GPU acceleration
            # Use better sampling parameters to reduce repetition
            # Allow longer generation for comprehensive reviews
            max_gen_tokens = min(max_tokens, 512)  # Increased from 200 to 512 for longer outputs
            
            outputs = self.local_pipeline(
                full_prompt,
                max_new_tokens=max_gen_tokens,  # Allow longer generation
                temperature=max(temperature, 0.7),  # Higher temperature reduces repetition
                do_sample=True,
                top_p=0.9,  # Nucleus sampling - better than top_k
                top_k=50,  # Limit vocabulary for better quality
                repetition_penalty=1.2,  # Penalize repetition
                pad_token_id=self.local_tokenizer.eos_token_id,
                return_full_text=False,
                truncation=True
            )
            
            # Extract generated text
            if isinstance(outputs, list) and len(outputs) > 0:
                generated_text = outputs[0].get("generated_text", "")
                # Post-process to remove repetition
                cleaned_text = self._remove_repetition(generated_text)
                return cleaned_text.strip()
            else:
                return str(outputs)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _remove_repetition(self, text: str, max_repeat: int = 2) -> str:
        """Remove excessive repetition from generated text"""
        if not text:
            return text
        
        # Split into sentences
        sentences = text.split('.')
        if len(sentences) < 2:
            return text
        
        # Remove consecutive duplicate sentences
        cleaned_sentences = []
        prev_sentence = None
        repeat_count = 0
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:  # Skip very short fragments
                continue
            
            # Normalize for comparison (lowercase, remove extra spaces)
            normalized = ' '.join(sentence.lower().split())
            
            # Skip if we've seen this exact sentence too many times
            if normalized in seen_sentences:
                repeat_count += 1
                if repeat_count > max_repeat:
                    continue  # Skip this repetition
            else:
                seen_sentences.add(normalized)
                repeat_count = 0
            
            cleaned_sentences.append(sentence)
            prev_sentence = sentence
        
        # Take first few sentences if output is too long (keep most relevant)
        if len(cleaned_sentences) > 8:
            cleaned_sentences = cleaned_sentences[:8]
        
        result = '. '.join(cleaned_sentences)
        if result and not result.endswith('.'):
            result += '.'
        
        return result


# Default client - uses GPU if available
def get_default_llm():
    """
    Get default LLM client with GPU support
    
    Priority:
    1. OpenAI API (if OPENAI_API_KEY env variable set)
    2. Ollama (uses GPU automatically if available)
    3. HuggingFace Inference API (if HUGGINGFACE_API_KEY env variable set)
    4. HuggingFace local (GPU/MPS if available, otherwise CPU)
    """
    # 1. Check if OpenAI API is configured and reachable
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("your_") and openai_key.strip() != "":
        try:
            import socket
            # Test host resolution and port connection to verify network availability
            socket.create_connection(("api.openai.com", 80), timeout=2)
            print("✓ Using OpenAI API backend")
            return LLMClient(
                backend="openai",
                model="gpt-4o-mini",
                api_key=openai_key
            )
        except Exception as e:
            print(f"⚠️ OpenAI connection failed ({e}). Trying next backend...")

    # 2. Check if Ollama is available and running
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=2)
        if result.returncode == 0:
            output_str = result.stdout.decode()
            # Select the appropriate model
            model_to_use = "llama3.2"
            if "llama3.2" in output_str:
                model_to_use = "llama3.2"
            elif "llama" in output_str:
                # Find the first model name with llama in it
                for line in output_str.splitlines():
                    if "llama" in line.lower():
                        model_to_use = line.split()[0]
                        break
            
            print(f"✓ Using Ollama backend with model: {model_to_use}")
            return LLMClient(
                backend="ollama",
                model=model_to_use,
                use_gpu=True
            )
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        print(f"Ollama not running or check failed: {e}")

    # 3. Check if Hugging Face Inference API is configured and reachable
    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_key and not hf_key.startswith("your_") and hf_key.strip() != "":
        try:
            import socket
            # Test host resolution and port connection to verify network availability
            socket.create_connection(("router.huggingface.co", 443), timeout=2)
            model_name = "mistralai/Mistral-7B-Instruct-v0.3"
            print(f"✓ Using Hugging Face Inference API backend with model: {model_name}")
            return LLMClient(
                backend="huggingface",
                model=model_name,
                api_key=hf_key
            )
        except Exception as e:
            print(f"⚠️ Hugging Face connection failed ({e}). Falling back...")
    
    # 4. Fallback: HuggingFace local (GPU/MPS)
    if TRANSFORMERS_AVAILABLE:
        use_gpu = CUDA_AVAILABLE or MPS_AVAILABLE
        device_name = DEVICE
        print(f"✓ Using HuggingFace local model on {device_name}")
        try:
            return LLMClient(
                backend="huggingface_local",
                model="gpt2",  # Fallback to gpt2
                use_gpu=use_gpu
            )
        except Exception as e:
            print(f"HuggingFace model loading failed: {e}")
    
    # Last resort
    print("⚠️  Warning: No local models available. Returning Ollama client default.")
    return LLMClient(backend="ollama", model="llama3.2", use_gpu=False)

