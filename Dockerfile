# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
# The Vite build needs the maps key to bake it into the HTML/JS
ARG VITE_GOOGLE_MAPS_API_KEY
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY
RUN npm run build


# Stage 2: Serve via FastAPI backend
FROM python:3.11-slim
WORKDIR /app/backend

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy the built React app into a static folder
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose port (Cloud Run sets PORT=8080 usually)
EXPOSE 8080

# Cloud Run injects the PORT env var dynamically
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
