# 🚀 Deployment Guide

## 🌐 Render Deployment (Recommended)

### Prerequisites
- GitHub repository with your code
- Render account ([sign up here](https://render.com))
- EURI API key

### Option 1: One-Click Deployment (Easiest)

1. **Fork this repository** to your GitHub account
2. **Click the Deploy button** (if available) or follow manual steps below

### Option 2: Manual Deployment

#### Step 1: Deploy Backend

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click "New" → "Web Service"

2. **Connect Repository**
   - Select "Build and deploy from a Git repository"
   - Connect your GitHub account
   - Select your forked repository

3. **Configure Backend Service**
   ```
   Name: pdf-rag-backend
   Environment: Python 3
   Build Command: cd backend && uv pip install -r requirements.txt
   Start Command: cd backend && python app/main.py
   ```

4. **Set Environment Variables**
   ```
   EURI_API_KEY=your_euri_api_key_here
   EURI_MODEL=euri-large
   EURI_EMBEDDING_MODEL=euri-embeddings
   HOST=0.0.0.0
   PORT=10000
   DATABASE_URL=sqlite:///./pdf_rag.db
   VECTOR_DB_TYPE=chroma
   LOG_LEVEL=INFO
   DEBUG=false
   ```

5. **Advanced Settings**
   - Instance Type: Standard (2GB RAM minimum)
   - Auto-Deploy: Yes
   - Health Check Path: `/docs`

#### Step 2: Deploy Frontend

1. **Create Static Site**
   - Click "New" → "Static Site"
   - Select same repository

2. **Configure Frontend Service**
   ```
   Name: pdf-rag-frontend
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/build
   ```

3. **Set Environment Variables**
   ```
   REACT_APP_API_URL=https://your-backend-service-name.onrender.com
   ESLINT_NO_DEV_ERRORS=true
   GENERATE_SOURCEMAP=false
   ```

#### Step 3: Update Frontend API URL

After backend deployment:
1. Copy your backend URL (e.g., `https://pdf-rag-backend.onrender.com`)
2. Update frontend environment variable:
   ```
   REACT_APP_API_URL=https://pdf-rag-backend.onrender.com
   ```
3. Redeploy frontend

### ✅ Verification

1. **Backend Health Check**
   - Visit: `https://your-backend-url.onrender.com/docs`
   - Should show: API documentation

2. **Frontend Access**
   - Visit: `https://your-frontend-url.onrender.com`
   - Should show: Professional UI with chat interface

3. **Full System Test**
   - Upload a PDF document
   - Ask questions about the document
   - Verify responses

## 🐳 Docker Deployment

### Local Docker Development

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Docker Deployment

```bash
# Build production images
docker build -t pdf-rag-backend ./backend
docker build -t pdf-rag-frontend ./frontend

# Run with production settings
docker run -d \
  --name pdf-rag-backend \
  -p 8000:10000 \
  -e EURI_API_KEY=your_key_here \
  pdf-rag-backend

docker run -d \
  --name pdf-rag-frontend \
  -p 3000:80 \
  -e REACT_APP_API_URL=http://localhost:8000 \
  pdf-rag-frontend
```

## 🔧 Environment Variables Reference

### Backend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EURI_API_KEY` | EURI AI API key | - | ✅ |
| `EURI_MODEL` | EURI model name | euri-large | ❌ |
| `EURI_EMBEDDING_MODEL` | Embedding model | euri-embeddings | ❌ |
| `HOST` | Server host | 0.0.0.0 | ❌ |
| `PORT` | Server port | 10000 | ❌ |
| `DATABASE_URL` | Database connection | sqlite:///./pdf_rag.db | ❌ |
| `VECTOR_DB_TYPE` | Vector database type | chroma | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |
| `DEBUG` | Debug mode | false | ❌ |

### Frontend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REACT_APP_API_URL` | Backend API URL | http://localhost:8000 | ✅ |
| `ESLINT_NO_DEV_ERRORS` | Disable ESLint errors | true | ❌ |
| `GENERATE_SOURCEMAP` | Generate source maps | false | ❌ |

## 🚨 Troubleshooting Deployment

### Common Issues

#### Backend fails to start
- Check environment variables are set correctly
- Verify EURI API key is valid
- Check logs for specific error messages

#### Frontend can't connect to backend
- Verify `REACT_APP_API_URL` points to correct backend URL
- Check CORS settings in backend
- Ensure backend is running and accessible

#### File upload fails
- Check file size limits
- Verify upload directory permissions
- Check available disk space

### Getting Help

1. Check Render logs in dashboard
2. Review error messages in browser console
3. Test API endpoints directly using `/docs`
4. Verify environment variables are set correctly

## 📊 Monitoring & Maintenance

### Health Checks
- Backend: `GET /docs` should return 200
- Frontend: Main page should load without errors

### Performance Monitoring
- Monitor response times in Render dashboard
- Check memory usage and scale if needed
- Monitor error rates and logs

### Updates & Maintenance
- Enable auto-deploy for automatic updates
- Monitor for security updates
- Regular backup of uploaded documents (if using persistent storage)
