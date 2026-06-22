#!/bin/bash
# ==========================================
# CyberShield-AI Google Cloud Deployment Script
# ==========================================
# This script is designed to be run in Google Cloud Shell.
# It will guide you through deploying your backend and frontend to Google Cloud Run.
#
# Before running this script, ensure you have:
# 1. Created a Google Cloud Project and selected it in Cloud Shell.
# 2. Enabled the "Cloud Run API", "Cloud Build API", and "Artifact Registry API".
# 3. Created an Artifact Registry repository for Docker images.
#
# Stop on any error
set -e

# --- STEP 1: Configuration ---
# We define some variables here to make the script reusable.
echo "=== Step 1: Setting up variables ==="
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="cybershield-repo"
BACKEND_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend:latest"
FRONTEND_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend:latest"

echo "Project ID: $PROJECT_ID"

# --- STEP 2: Enable necessary Google Cloud APIs ---
echo "=== Step 2: Enabling Google Cloud APIs ==="
# Cloud Run needs these APIs to build and run your containers.
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# --- STEP 3: Create an Artifact Registry Repository ---
echo "=== Step 3: Setting up Artifact Registry ==="
# This is where your built Docker images will be stored (like a private Docker Hub).
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION > /dev/null 2>&1; then
    echo "Creating Artifact Registry repository '$REPO_NAME'..."
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Docker repository for CyberShield-AI"
else
    echo "Repository '$REPO_NAME' already exists."
fi

# --- STEP 4: Build and Deploy the Backend ---
echo "=== Step 4: Building and Deploying Backend ==="
# We use Cloud Build to build the Docker image in the cloud. No local Docker required!
echo "Building backend image..."
gcloud builds submit --tag $BACKEND_IMAGE .

# Deploying the built image to Cloud Run.
# We set --allow-unauthenticated so anyone on the web can access the API.
echo "Deploying backend to Cloud Run..."
gcloud run deploy cybershield-backend \
    --image $BACKEND_IMAGE \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8000

# After deployment, we fetch the URL Google generated for your backend.
BACKEND_URL=$(gcloud run services describe cybershield-backend \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo "Backend deployed successfully! URL: $BACKEND_URL"

# --- STEP 5: Build and Deploy the Frontend ---
echo "=== Step 5: Building and Deploying Frontend ==="
# We move into the frontend directory.
cd frontend

# The frontend needs to know where the backend is to make API requests.
# We pass the $BACKEND_URL we just got as a build argument.
echo "Building frontend image..."
gcloud builds submit --tag $FRONTEND_IMAGE \
    --build-arg=VITE_API_URL=$BACKEND_URL .

# Deploying the frontend to Cloud Run.
echo "Deploying frontend to Cloud Run..."
gcloud run deploy cybershield-frontend \
    --image $FRONTEND_IMAGE \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 80

# Fetch the final frontend URL
FRONTEND_URL=$(gcloud run services describe cybershield-frontend \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo "=========================================="
echo "Deployment Complete!"
echo "Your frontend is live at: $FRONTEND_URL"
echo "Your backend is live at: $BACKEND_URL"
echo "=========================================="
