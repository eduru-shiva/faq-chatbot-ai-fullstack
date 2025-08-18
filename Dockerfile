# ---------- Frontend Build ----------
FROM node:18 AS frontend-build
WORKDIR /frontend

# Copy only package files first for caching
COPY react-app/package.json react-app/package-lock.json ./
RUN npm install

# Copy all frontend code and build
COPY react-app/ ./
RUN npm run build

# ---------- Backend Setup ----------
FROM python:3.9-slim
WORKDIR /app

# Install system build tools (needed for some Python packages)
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Upgrade pip & install Python dependencies
COPY requirements.txt . 
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy frontend build from previous stage
COPY --from=frontend-build /frontend/dist ./frontend_dist

# Expose backend port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
