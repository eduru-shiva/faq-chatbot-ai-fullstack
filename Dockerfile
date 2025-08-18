# ---------- Frontend Build ----------
FROM node:20 AS frontend-build
WORKDIR /frontend
COPY react-app/package.json react-app/package-lock.json ./
RUN npm install
COPY react-app/ .
RUN npm run build   # builds React -> dist/

# ---------- Backend Setup ----------
FROM python:3.9-slim
WORKDIR /app

# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + frontend build
COPY . .
COPY --from=frontend-build /frontend/dist ./frontend_dist

# Expose backend port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
