<!-- Recommended folder structure -->

flipkart-clone/
├── frontend/                  # Next.js 14
│   ├── app/
│   │   ├── (auth)/
│   │   ├── products/
│   │   ├── cart/
│   │   └── seller/
│   └── components/
│
├── backend/                   # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── orders.py
│   │   │   └── seller.py
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── core/
│   │       ├── config.py
│   │       └── database.py
│   ├── requirements.txt
│   └── Dockerfile
│
└── docker-compose.yml




Flipkart clone — full stack architecture
Frontend
Next.js 14 (App Router)
SSR / SSG pages
React Query
Tailwind CSS
Zustand (state)
Razorpay / Stripe (payments)
Backend
FastAPI (Python 3.11+)
REST APIs
JWT Auth
SQLAlchemy ORM
Pydantic
Celery + Redis (async tasks)
REST
Data Layer
MySQL
Primary DB
Users, Orders, Products
Redis
Cache + Sessions
Cart, OTP, Rate limit
Elasticsearch
Search Engine
Product search, filters
Core service modules
Auth
Login, OTP, OAuth
Catalogue
Products, variants
Cart + Orders
Checkout, invoice
Seller Panel
Listings, inventory
Payments
Razorpay, refunds
Reviews
Ratings, Q&A
Notifications
Email, SMS, push
Delivery
Tracking, logistics
Infrastructure + DevOps
Docker
Containerise all services
GitHub Actions
CI/CD pipeline
AWS / Railway
Deploy backend
Vercel
Deploy Next.js
Storage + CDN
AWS S3
Images, files
CloudFront CDN
Fast media delivery

