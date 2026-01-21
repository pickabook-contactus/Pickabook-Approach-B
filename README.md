# 📚 PickaBook: Magic of Money (Approach B)

PickaBook is a personalized children's book generator. This repository contains **Approach B**, specifically tailored for the **"Magic of Money"** book, featuring multi-character composition (Mom & Child).

## 🌟 Features

- **Multi-Character Support**: Automatically composites dynamic "Mom" and "Child" characters into storybook pages.
- **Smart Composition**: Uses a coordinate-based slot system (`slot.json`) to place photos perfectly on every page.
- **Simple Mode**: Bypasses complex AI generation for speed/reliability, focusing on high-quality compositing of user uploads.
- **Production Ready**: Configured for deployment on **Render** (Backend) and **Vercel** (Frontend).

---

## 🏗️ Project Structure

- **`frontend/`**: Next.js 14 App Router application. Handles User Interface, Uploads, and Order Status.
- **`backend/`**: FastAPI (Python 3.11). Handles API, Image Processing (Pillow), and Celery Background Tasks.
- **`backend/assets/templates/`**: Storage for book assets (`bg.png`, `slot.json`).

---

## 🚀 Deployment

The project is designed to be cost-effective (Free Tier compatible).

### Deployment Architecture
- **Backend + Worker**: Deployed on [Render](https://render.com).
- **Frontend**: Deployed on [Vercel](https://vercel.com).
- **Database**: External Postgres (e.g., [Supabase](https://supabase.com)).
- **Queue**: External Redis (e.g., [Upstash](https://upstash.com)).

### How to Deploy
See the detailed [**Deployment Guide**](./DEPLOYMENT_GUIDE.md) included in this repository.

1.  **Push to GitHub**.
2.  **Create Render Web Service**: Connect Repo -> Select `render.yaml`.
3.  **Set Environment Variables**: `DATABASE_URL`, `REDIS_URL`.

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (Local or Cloud)
- Postgres (Local or Cloud)

### Quick Start
1.  **Backend**:
    ```bash
    cd backend
    pip install -r requirements.txt
    # Start Backend & Worker
    ./start_free_tier.sh
    ```
2.  **Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
3.  **Visit**: `http://localhost:3000/create`

---

## 📄 License
Private Repository for PickaBook ContactUs.
