# Hugging Face Inference API Setup Guide

This guide explains how to configure and run the Multi-Agent Research Paper Reviewer using the free, serverless **Hugging Face Inference API** instead of local Ollama or HuggingFace transformers.

---

## Why use the Hugging Face Inference API?
* **Zero local hardware requirements:** No local GPU or high RAM/CPU usage is required.
* **Serverless and free:** The serverless inference endpoint is completely free for testing and demoing.
* **Easy cloud deployment:** Highly recommended when deploying to **Streamlit Community Cloud** or other host environments where running local models is not possible.

---

## Step 1: Get a Hugging Face API Key (Access Token)
1. Go to [huggingface.co](https://huggingface.co) and sign in (or create a free account).
2. Navigate to your **Profile Settings** -> **Access Tokens** (or visit [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
3. Click **New token**.
4. Set the **Token Name** (e.g., `paper-reviewer`) and choose **Read** role.
5. Click **Generate a token** and copy it.

---

## Step 2: Configure your `.env` File
In the root directory of the project, create or open the `.env` file. Paste your token like this:

```bash
# HuggingFace Inference API Key (Free Serverless API)
HUGGINGFACE_API_KEY=hf_your_token_here
```
*(Replace `hf_your_token_here` with the token you copied in Step 1).*

---

## Step 3: Start the Streamlit Application
Run the Streamlit server using your conda environment:

```bash
conda activate multi
streamlit run app.py
```

---

## How it works under the hood
1. When the application starts, the `llm_client.py` scans for the `HUGGINGFACE_API_KEY` environment variable.
2. If detected, it automatically overrides local backends and routes all requests to Hugging Face’s cloud servers.
3. The default model used is **`mistralai/Mistral-7B-Instruct-v0.3`**, which is highly capable at instruction following and summarization.

---

## Verify it is working
Check the **System Info** card on the sidebar of the Streamlit interface. It should dynamically update to show:
* **LLM Backend:** `Huggingface (mistralai/Mistral-7B-Instruct-v0.3)`
* **GPU Support:** `Disabled (CPU)` (Since processing is handled on Hugging Face's cloud servers).
