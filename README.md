# Smart Resume Builder & Job Matcher

A production-grade full-stack application that helps users build professional resumes, optimize them with AI, match with job postings, and prepare for interviews.

## 🚀 Project Overview

This application combines:
- **AI-Powered Resume Building**: Create and customize professional resumes with multiple templates
- **Job Matching**: Intelligent job matching using vector search and AI analysis
- **Resume Optimization**: Get AI-powered suggestions to improve your resume
- **Cover Letter Generation**: Automatically generate tailored cover letters
- **Interview Preparation**: AI-powered interview question practice

## 🏗️ Tech Stack

### Backend
- **Django** + **Django REST Framework**: API backend
- **PostgreSQL**: Primary database (via Supabase)
- **Supabase**: Database, authentication, and storage
- **OpenAI + LangChain**: AI capabilities for resume optimization and job matching
- **Pinecone**: Vector database for semantic job search
- **Celery + Redis**: Background task processing
- **Gunicorn**: Production WSGI server

### Frontend
- **Next.js 14+**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Styling
- **Framer Motion**: Animations
- **React Hook Form + Zod**: Form handling and validation
- **TanStack Query**: Data fetching and caching
- **Radix UI**: Accessible component primitives

## 📁 Project Structure

```
resume-ai-pro/
├── backend/          # Django REST API
│   ├── config/       # Django settings
│   ├── api/          # Core API app
│   ├── resumes/      # Resume management
│   ├── jobs/         # Job posting & matching
│   ├── users/        # User profiles
│   └── ai/           # AI services
├── frontend/         # Next.js application
│   ├── src/
│   │   ├── app/      # App router pages
│   │   ├── components/
│   │   └── lib/
└── README.md
```

## 🔀 Branch Strategy

- **main**: Production-ready code
- **backend**: Backend development
- **frontend**: Frontend development
- **ci-cd**: CI/CD configuration and workflows

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11+
- Poetry (Python package manager)
- Node.js 18+
- pnpm (package manager)
- PostgreSQL (or Supabase account)
- Redis (for Celery)

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Fill in `.env` with your credentials:
   - Django secret key
   - Database URL (Supabase PostgreSQL)
   - Supabase credentials
   - OpenAI API key
   - Pinecone credentials
   - Redis URL

5. Run migrations:
   ```bash
   poetry run python manage.py migrate
   ```

6. Create superuser:
   ```bash
   poetry run python manage.py createsuperuser
   ```

7. Seed resume templates:
   ```bash
   poetry run python manage.py seed_templates
   ```

8. Run development server:
   ```bash
   poetry run python manage.py runserver
   ```

9. Start Celery worker (in separate terminal):
   ```bash
   poetry run celery -A config worker -l info
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env.local
   ```

4. Fill in `.env.local` with your API URLs and keys

5. Run development server:
   ```bash
   pnpm dev
   ```

6. Open [http://localhost:3000](http://localhost:3000)

## 📚 API Documentation

Once the backend is running, access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`

## 🧪 Testing

### Backend Tests
```bash
cd backend
poetry run pytest
```

### Frontend Tests
```bash
cd frontend
pnpm test
```

## 🚢 Deployment

### Backend
- Use Gunicorn for production: `gunicorn config.wsgi:application`
- Set up environment variables on your hosting platform
- Configure static files with WhiteNoise
- Set up Celery workers and Redis

### Frontend
- Build: `pnpm build`
- Deploy to Vercel, Netlify, or your preferred platform
- Configure environment variables

## 🔐 Environment Variables

See `.env.example` files in both `backend/` and `frontend/` directories for required environment variables.

## 📝 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines]

## 🔗 Live Demo

[Add your live demo link here once deployed]

## 📧 Contact

[Your Contact Information]

