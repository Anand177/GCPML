# Docker build
docker build -t cr-ml-lr-houseprice:v1 .

# Configure Docker Auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push to Artifact Registry
docker tag cr-ml-lr-houseprice:v1 us-central1-docker.pkg.dev/gcp-project-375309/anand-docker-repo/cr-ml-lr-houseprice:v1
docker push us-central1-docker.pkg.dev/gcp-project-375309/anand-docker-repo/cr-ml-lr-houseprice:v1

# Deploy to Cloud Run
gcloud run deploy cr-ml-lr-houseprice \
  --image=us-central1-docker.pkg.dev/gcp-project-375309/anand-docker-repo/cr-ml-lr-houseprice:v1 \
  --region=us-central1 \
  --service-account=cloudrun-bq-sa@gcp-project-375309.iam.gserviceaccount.com \
  --port=8080 \
  --allow-unauthenticated