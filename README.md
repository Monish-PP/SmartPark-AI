# SmartPark AI 🚗🤖

**AI-powered smart parking marketplace connecting drivers with private parking owners.**

---

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | React 18, Tailwind CSS, Redux Toolkit, Framer Motion, Chart.js |
| Backend | Django 5.2, DRF, JWT Auth, Celery |
| Database | MongoDB Atlas (django-mongodb-backend + pymongo / motor) |
| AI/CV | YOLOv8 (ultralytics), OpenCV, TensorFlow/Keras |
| ML | Scikit-learn (KNN), XGBoost, Random Forest |
| Forecasting | LSTM, Prophet, XGBoost |
| Fraud | Isolation Forest |
| Payments | Razorpay |
| Notifications | Firebase Cloud Messaging |
| Maps | Google Maps API (Geocoding, Heatmap, Directions) |
| Cache | Redis |
| Storage | Supabase |
| Deploy | Vercel (Frontend), Render/AWS (Backend), Docker |

---

## Project Structure
```
smartpark-ai/
├── frontend/            # React + Tailwind app
│   └── src/
│       ├── components/  # Navbar, ParkingCard, LiveHeatmap
│       ├── pages/       # Landing, Search, Book, Bookings, Owner, Admin
│       ├── store/       # Redux slices (auth, parking)
│       └── services/    # Axios API layer
├── backend/
│   ├── smartpark/       # Django project (settings, urls, celery)
│   ├── apps/
│   │   ├── users/       # Auth, JWT, Vehicles
│   │   ├── parking/     # Lots, Slots, Schedules, Occupancy
│   │   ├── bookings/    # Bookings, Payments, Reviews
│   │   ├── analytics/   # Owner Dashboard, Admin, Heatmap, Forecast
│   │   └── notifications/
│   └── ai_engine/
│       ├── recommendation/  # KNN + RF + XGBoost ensemble
│       ├── occupancy/       # YOLOv8 + OpenCV + PKLot trainer
│       ├── forecasting/     # LSTM + Prophet + XGBoost
│       └── fraud/           # Isolation Forest
├── ml_models/           # Trained model artifacts (.pt, .pkl)
└── docker/              # Dockerfiles + docker-compose.yml
```

---

## Quick Start

### 1. Backend Setup
```bash
cd backend
cp .env.example .env          # Fill in your credentials
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 2. Frontend Setup
```bash
cd frontend
cp .env.example .env.local    # Add your API keys
npm install
npm run dev
```

### 3. Redis & Celery
```bash
# Terminal 1: Redis (or use Docker)
redis-server

# Terminal 2: Celery worker
cd backend
celery -A smartpark worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A smartpark beat --loglevel=info
```

### 4. Docker (all-in-one)
```bash
cd docker
docker-compose up --build
```

---

## YOLOv8 Training on PKLot Dataset

```bash
# Step 1: Download PKLot dataset
# From: https://universe.roboflow.com/brad-dwyer/pklot-1tros
# Or: https://web.inf.ufpr.br/vri/databases/parking-lot-database/

# Step 2: Convert + Train
cd backend
python ai_engine/occupancy/train_yolo.py \
    --raw_dir /path/to/PKLot \
    --epochs 50 \
    --batch 16 \
    --output ml_models/
```
Trained model is saved to `ml_models/yolov8_parking.pt`.

---

## Training ML Models

```python
# Recommender (run from backend/)
from ai_engine.recommendation.engine import train_recommender
import pandas as pd
df = pd.read_csv("data/historical_bookings.csv")
train_recommender(df, save_dir="ml_models/")

# Demand Forecaster
from ai_engine.forecasting.forecaster import train_lstm, train_prophet, train_xgboost_forecaster
df = pd.read_csv("data/occupancy_logs.csv")
train_lstm(df)
train_prophet(df)
train_xgboost_forecaster(df)

# Fraud Detector
from ai_engine.fraud.detector import train_fraud_model
df = pd.read_csv("data/user_behaviour.csv")
train_fraud_model(df)
```

---

## Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register user/owner |
| POST | `/api/auth/login/` | JWT login |
| GET  | `/api/parking/search/` | AI-powered parking search |
| POST | `/api/bookings/create/` | Create booking + Razorpay order |
| POST | `/api/bookings/{id}/entry/` | Mark vehicle entry |
| POST | `/api/bookings/{id}/exit/` | Mark exit, compute refund |
| POST | `/api/bookings/verify-payment/` | Razorpay webhook |
| GET  | `/api/analytics/owner/` | Owner dashboard |
| GET  | `/api/analytics/heatmap/` | Live demand heatmap |
| GET  | `/api/analytics/forecast/{lot}/` | 24h demand forecast |

**Swagger docs**: http://localhost:8000/swagger/

---

## License
MIT © SmartPark AI Team
# SmartPark-AI
