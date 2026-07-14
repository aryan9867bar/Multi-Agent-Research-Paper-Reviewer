#!/bin/bash
# Quick deployment script for Streamlit Cloud

echo "🚀 Preparing for Streamlit Cloud Deployment..."
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo "⚠️  No git remote found. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo ""
    read -p "Enter your GitHub repository URL (or press Enter to skip): " repo_url
    if [ ! -z "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "✓ Remote added: $repo_url"
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "📝 Staging changes..."
    git add .
    
    echo "💾 Committing changes..."
    git commit -m "Deploy multi-agent paper reviewer to Streamlit Cloud"
    echo "✓ Changes committed"
else
    echo "✓ No uncommitted changes"
fi

# Show current status
echo ""
echo "📊 Current git status:"
git status --short

echo ""
echo "✅ Ready to push to GitHub!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "2. Go to https://streamlit.io/cloud"
echo "3. Click 'New app'"
echo "4. Select your repository"
echo "5. Set main file path to: app.py"
echo "6. Click 'Deploy'"
echo ""
echo "Your app will be live at: https://<your-app-name>.streamlit.app"

