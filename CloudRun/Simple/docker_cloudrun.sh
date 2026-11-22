# Docker build
docker build -t cloud-run-simple:v1 .

# Configure Docker Auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push to Artifact Registry
docker tag cloud-run-simple:v1 us-central1-docker.pkg.dev/gcp-project-375309/anand-docker-repo/cloud-run-simple:v1
docker push us-central1-docker.pkg.dev/gcp-project-375309/anand-docker-repo/cloud-run-simple:v1

# Deploy to Cloud Run
gcloud run deploy cloud-run-simple \
  --image=us-central1-docker.pkg.dev/gcp-project-375309/anand-docker-repo/cloud-run-simple:v1 \
  --region=us-central1 \
  --service-account=cloudrun-bq-sa@gcp-project-375309.iam.gserviceaccount.com \
  --port=5052 \
  --allow-unauthenticated