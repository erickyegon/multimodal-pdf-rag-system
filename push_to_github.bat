@echo off
echo 🚀 Pushing Multimodal PDF RAG System to GitHub...
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Initialize git repository
echo ⚙️ Initializing Git repository...
git init

REM Add remote repository
echo 🔗 Adding GitHub remote...
git remote add origin https://github.com/erickyegon/multimodal-pdf-rag-system.git

REM Stage all files
echo 📁 Staging all files...
git add .

REM Show status
echo 📊 Git status:
git status

REM Commit changes
echo 💾 Committing changes...
git commit -m "🚀 Initial commit: Complete Multimodal PDF RAG System

✅ Features:
- Professional React UI with chat interface
- FastAPI backend with comprehensive PDF processing
- OCR integration with Tesseract
- Table extraction and multimodal content processing
- EURI AI integration with retry logic
- Vector database with ChromaDB
- Analytics dashboard and document management
- Render deployment configuration
- Comprehensive documentation and deployment guides

🔧 Fixes Applied:
- Missing dependencies (psutil, python-multipart, tenacity)
- Tesseract OCR path detection for Windows/Linux/macOS
- DataFrame duplicate column handling
- Frontend API configuration with fallbacks
- Error handling and graceful degradation

🌐 Deployment Ready:
- Docker configuration for both frontend and backend
- Render deployment files (render.yaml, Dockerfiles)
- Environment configuration templates
- Comprehensive README and deployment guides"

REM Set main branch and push
echo 🚀 Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ✅ Successfully pushed to GitHub!
echo 🌐 Visit: https://github.com/erickyegon/multimodal-pdf-rag-system
echo.
pause
