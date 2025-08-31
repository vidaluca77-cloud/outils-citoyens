# Deployment Instructions

## Vercel Deployment

### Prerequisites
- Vercel account
- API deployed separately (e.g., on Render, Fly.io, or Railway)

### Steps

1. **Deploy the API first** (using Render, Fly.io, or similar):
   - Upload the `api/` directory 
   - Set environment variable `OPENAI_API_KEY` (optional, falls back to mock)
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Deploy the web application on Vercel**:
   - Connect your GitHub repository to Vercel
   - Set the root directory to `web/`
   - Configure environment variables:
     - `NEXT_PUBLIC_API_BASE`: Your deployed API URL (e.g., `https://your-api.onrender.com`)
   - Vercel will automatically detect it's a Next.js app and deploy

### Environment Variables

#### Web Application (.env.local)
```
NEXT_PUBLIC_API_BASE=https://your-deployed-api-url.com
```

#### API Application
```
OPENAI_API_KEY=your-openai-key-here  # Optional - falls back to mock responses
```

### Verification

After deployment:
1. Test the health endpoint: `https://your-api-url.com/health`
2. Test the web application loads at your Vercel URL
3. Test form submission on any tool (e.g., `/outil/amendes`)

## Manual Deployment

### Build locally
```bash
cd web/
npm install
npm run build
npm start
```

### API locally
```bash
cd api/
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```