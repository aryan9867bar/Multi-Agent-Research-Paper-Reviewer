# Streamlit Cloud Deployment Guide

This guide explains how to deploy the Multi-Agent Research Paper Reviewer on Streamlit Cloud.

## Option 1: Streamlit Cloud (Recommended - Free)

Streamlit Cloud provides free hosting for Streamlit apps. However, note that:
- **No GPU support** - Models will run on CPU (slower)
- **Memory limits** - Large models may not fit
- **Recommended**: Use API-based LLMs (OpenAI, HuggingFace Inference API) for best performance

### Steps to Deploy:

1. **Push your code to GitHub**
   ```bash
   cd Multi-Agent-Research-Paper-Reviewer
   git init  # if not already a git repo
   git add .
   git commit -m "Deploy multi-agent paper reviewer"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Go to [Streamlit Cloud](https://streamlit.io/cloud)**
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set:
     - **Main file path**: `app.py`
     - **Python version**: 3.9 or 3.10
     - **Branch**: `main` (or your default branch)

3. **Configure Environment Variables** (if using API keys):
   - Go to "Advanced settings"
   - Add environment variables:
     - `OPENAI_API_KEY` (if using OpenAI)
     - `HUGGINGFACE_API_KEY` (if using HF Inference API)

4. **Deploy!**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at: `https://<your-app-name>.streamlit.app`

### For CPU-Only Deployment (Streamlit Cloud):

The app will automatically:
- Detect no GPU and fall back to CPU
- Use lightweight models (distilgpt2) if available
- Or use API-based LLMs if configured

**Recommended**: Set up OpenAI API or HuggingFace Inference API for better performance on Streamlit Cloud.

## Option 2: Self-Hosted with ngrok (For GPU Access)

If you want to use your GPU server and share the link:

1. **Install ngrok**:
   ```bash
   # Download from https://ngrok.com/download
   # Or use snap
   sudo snap install ngrok
   ```

2. **Run Streamlit**:
   ```bash
   cd Multi-Agent-Research-Paper-Reviewer
   streamlit run app.py --server.port=8501
   ```

3. **Create ngrok tunnel**:
   ```bash
   ngrok http 8501
   ```

4. **Share the ngrok URL** (e.g., `https://abc123.ngrok.io`)

**Note**: Free ngrok URLs expire after 2 hours. For permanent URLs, upgrade to paid plan.

## Option 3: Deploy on Your Own Server

If you have a server with a public IP:

1. **Run Streamlit**:
   ```bash
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   ```

2. **Configure firewall** to allow port 8501

3. **Access via**: `http://<your-server-ip>:8501`

## Configuration for Different Environments

### For Streamlit Cloud (CPU-only):
- The app automatically detects CPU-only environment
- Uses lightweight models or API-based LLMs
- No configuration needed

### For GPU Server:
- Automatically uses GPU if available
- Uses GPT-2 Medium or larger models
- Full GPU acceleration enabled

## Troubleshooting

### Build Fails on Streamlit Cloud:
- Check that all dependencies in `requirements.txt` are compatible
- Ensure Python version is 3.9 or 3.10
- Check build logs for specific errors

### App Runs but Models Don't Load:
- Streamlit Cloud has limited memory (~1GB)
- Use API-based LLMs instead of local models
- Or use very lightweight models (distilgpt2)

### Slow Performance:
- Normal on CPU-only environments
- Consider using API-based LLMs for better performance
- Or deploy on GPU server with ngrok

## Quick Test After Deployment

1. Open your deployed app URL
2. Try the "Quick Test" button
3. Or enter an Arxiv ID: `1706.03762`
4. Check that reviews are generated successfully



# Streamlit Deployment Files

This folder contains all files needed for deploying the Multi-Agent Research Paper Reviewer to Streamlit Cloud.

## Files in this folder:

1. **README.md** - Step-by-step deployment guide
2. **deploy.sh** - Helper script for deployment
3. **.streamlit/config.toml** - Streamlit configuration file
4. **.gitignore** - Git ignore file

## Important: File Placement for Deployment

For Streamlit Cloud to work properly, some files need to be in the **root directory** of your project:

### Files that MUST be in root (`Multi-Agent-Research-Paper-Reviewer/`):
- `.streamlit/config.toml` - Streamlit looks for this in the root
- `.gitignore` - Git looks for this in the root
- `app.py` - Main Streamlit app (already in root)
- `requirements.txt` - Dependencies file (already in root)

### Files that can stay here (documentation):
- `README.md` - Reference guide
- `deploy.sh` - Helper script (can be run from anywhere)

## Quick Setup

1. **Copy required files to root**:
   ```bash
   # Copy Streamlit config
   cp -r .streamlit ../
   
   # Copy .gitignore
   cp .gitignore ../
   ```

2. **Follow instructions in `README.md`**

3. **Or run the deploy script**:
   ```bash
   ./deploy.sh
   ```

## Deployment Steps Summary

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Click "New app"
4. Select repository
5. Set main file: `app.py`
6. Deploy!

Your app will be live at: `https://<your-app-name>.streamlit.app`



# Quick Setup for Streamlit Cloud

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your code is in a GitHub repository:

```bash
cd Multi-Agent-Research-Paper-Reviewer

# Initialize git if needed
git init

# Add all files
git add .

# Commit
git commit -m "Deploy multi-agent paper reviewer to Streamlit Cloud"

# Add remote (replace with your GitHub repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. **Go to [streamlit.io/cloud](https://streamlit.io/cloud)**
   - Sign in with your GitHub account
   - Authorize Streamlit Cloud to access your repositories

2. **Click "New app"**

3. **Fill in the details:**
   - **Repository**: Select your repository
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`
   - **Python version**: `3.10` (recommended)

4. **Click "Deploy"**

5. **Wait for deployment** (usually 2-3 minutes)

6. **Your app will be live at**: `https://<your-app-name>.streamlit.app`

### 3. Important Notes for Streamlit Cloud

**Limitations:**
- ❌ **No GPU** - Models run on CPU (slower)
- ❌ **Limited memory** (~1GB) - Large models may not fit
- ✅ **Free hosting** - No cost
- ✅ **Automatic HTTPS** - Secure by default

**Recommended Setup:**
- Use **API-based LLMs** (OpenAI, HuggingFace Inference API) for best performance
- Or use lightweight models (distilgpt2) that work on CPU

### 4. Optional: Configure API Keys (For Better Performance)

If you want to use OpenAI or HuggingFace Inference API:

1. Go to your app settings on Streamlit Cloud
2. Click "Secrets"
3. Add:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
   or
   ```
   HUGGINGFACE_API_KEY=your-api-key-here
   ```

4. Update `agents/llm_client.py` to use these APIs if keys are available

### 5. Test Your Deployment

1. Open your app URL
2. Try the "Quick Test" button
3. Or enter an Arxiv ID: `1706.03762`
4. Verify reviews are generated

### Troubleshooting

**Build fails:**
- Check `requirements.txt` - all dependencies must be compatible
- Ensure Python version is 3.9 or 3.10
- Check build logs for specific errors

**App loads but models don't work:**
- Normal on CPU-only - use API-based LLMs
- Or accept slower performance with CPU models

**Slow performance:**
- Expected on CPU-only environments
- Consider using API-based LLMs
- Or deploy on your own GPU server with ngrok (see DEPLOYMENT.md)

## Alternative: Deploy on Your GPU Server with ngrok

If you want to use your GPU server and share a link:

```bash
# 1. Install ngrok (if not installed)
# Download from https://ngrok.com/download

# 2. Run Streamlit
cd /raid/home/rishabh/GenAI-Assignment2/part2_multi_agent
streamlit run app.py --server.port=8501

# 3. In another terminal, create ngrok tunnel
ngrok http 8501

# 4. Share the ngrok URL (e.g., https://abc123.ngrok.io)
```

**Note**: Free ngrok URLs expire after 2 hours. For permanent URLs, upgrade to paid plan.
