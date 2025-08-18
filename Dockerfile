# ---------- Frontend Build ----------
FROM node:18 AS frontend-build
WORKDIR /frontend

# Copy package files and install frontend dependencies
COPY react-app/package.json react-app/package-lock.json ./
RUN npm install

# Copy frontend source and build
COPY react-app/ .
RUN npm run build

# ---------- Backend Setup ----------
FROM python:3.9-slim
WORKDIR /app

# Install system build tools (required for some Python packages)
RUN apt-get update && apt-get install -y build-essential curl

# Upgrade pip and install backend dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy frontend build into backend static folder
COPY --from=frontend-build /frontend/dist ./frontend_dist

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
