# Deployment Directory

This directory contains the scripts and configuration needed to deploy the Project Agora agent to Google Cloud. You have two deployment options:

1. **Vertex AI Agent Engine** - Deploy as a managed reasoning engine service
2. **Cloud Run with Dev UI** - Deploy with a web interface for development and testing

## Which Deployment Option to Choose?

| Feature                       | Vertex AI Agent Engine                                    | Cloud Run with Dev UI                               |
| ----------------------------- | --------------------------------------------------------- | --------------------------------------------------- |
| **Primary Use Case**          | Production, API-driven integration                        | Development, Interactive Testing, Demos             |
| **Interface**                 | API only                                                  | Web UI & API                                        |
| **Management**                | Fully managed by Vertex AI                                | Serverless container managed by you                 |
| **Best For**                  | Building scalable backend services for other applications | Rapidly iterating and demonstrating agent behavior  |

## Overview

The deployment process offers two different approaches depending on your needs:

- **Agent Engine Deployment**: For production use as a managed service that can be integrated into other applications
- **Cloud Run Deployment**: For development, testing, and interactive use with a web interface

## Deployment Options

### Option 1: Vertex AI Agent Engine Deployment

Deploy the agent as a managed reasoning engine using `deploy_agent_engine.py`. This creates a serverless, scalable endpoint that other applications can integrate with.

#### Features

-   **Automated Packaging:** Automatically builds the agent's Python wheel (`.whl`) file using `poetry build`.
-   **Managed Service:** Deploys to Vertex AI Agent Engine as a fully managed reasoning engine.
-   **Environment Configuration:** Passes necessary environment variables (like RAG Corpus name and BigQuery details) from your local `.env` file to the cloud environment.
-   **Agent Management:** Provides commands to create and delete agent instances.

#### Prerequisites

1.  Complete all steps in the main project `README.md`, including running the `setup_environment.sh` script. This ensures your `.env` file is fully populated with the `RAG_CORPUS_NAME` and other necessary values.
2.  Authenticate with Google Cloud with sufficient permissions to manage Vertex AI and IAM resources.
3.  **Install Playwright Dependencies:** The `generate_diagram_from_mermaid` tool relies on Playwright. Ensure its system-level browser dependencies are installed by running the following command in your environment **before deploying**:
    ```bash
    npx playwright install --with-deps
    ```

#### How to Use

##### To Deploy a New Agent:

From the project's root directory, run:

```bash
python3 deployment/deploy_agent_engine.py --create
```

The script will:
1.  Build the application wheel file.
2.  Connect to your configured GCP project.
3.  Deploy the agent to Vertex AI Agent Engine.
4.  Print the full resource name of the deployed agent upon success.

Example output:
```
✅ Agent deployed successfully!
Resource Name: projects/your-gcp-project-id/locations/us-central1/reasoningEngines/1234567890123456789
```

##### To Delete a Deployed Agent:

You will need the full resource name of the agent you wish to delete:

```bash
python3 deployment/deploy_agent_engine.py --delete --resource_id "projects/your-gcp-project-id/locations/us-central1/reasoningEngines/1234567890123456789"
```

### Option 2: Cloud Run Deployment with Dev UI

Deploy the agent to Cloud Run with a web interface using `deploy_cloud_run.sh`. This option includes a development UI for interactive testing and development.

#### Features

-   **Web Interface:** Includes a development UI for interactive agent testing
-   **Cloud Run Deployment:** Serverless container deployment with automatic scaling
-   **API Integration:** Provides both UI and API endpoints
-   **Development Friendly:** Ideal for testing, debugging, and demonstrations

#### Prerequisites

1.  Complete all steps in the main project `README.md`, including running `setup_environment.sh`.
2.  Install the Google ADK CLI and authenticate with Google Cloud.
3.  **Install Playwright Dependencies:** The `generate_diagram_from_mermaid` tool relies on Playwright. For Cloud Run deployment, the underlying container environment must have these dependencies. The `playwright` Python package handles this, but for local testing prior to deployment, ensure you have run:
    ```bash
    npx playwright install --with-deps
    ```

#### How to Use

From the project's root directory, run:

```bash
bash deployment/deploy_cloud_run.sh
```

The script will:
1. Load environment variables from your `.env` file
2. Enable required Google Cloud APIs
3. Build and deploy the agent to Cloud Run
4. Provide URLs for accessing the deployed service

Upon successful deployment, you'll receive:
- Console URL for monitoring the service
- Command to get the service URL for accessing the web interface

## Environment Variables

Both deployment options require the following environment variables to be set in your `.env` file:

- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `GOOGLE_CLOUD_LOCATION`: Deployment region (e.g., us-central1)
- `RAG_CORPUS_NAME`: Name of your RAG corpus
- `BQ_PROJECT_ID`: BigQuery project ID
- `BQ_DATASET_ID`: BigQuery dataset ID

Additional variables for Cloud Run deployment:
- `GOOGLE_CLOUD_STORAGE_BUCKET`: GCS bucket for staging (Agent Engine only)
- `SERVICE_NAME`: Cloud Run service name (optional, defaults to "project-agora")

---

## Verifying Your Deployment

After deploying, you can test your endpoint to ensure it's running correctly.

### For Agent Engine:
Use the `gcloud` command to send a query. You will need the `REASONING_ENGINE_ID` from the deployment output.

```bash
gcloud alpha vertex ai reasoning-engines query REASONING_ENGINE_ID \
  --project="your-gcp-project-id" \
  --location="us-central1" \
  --query="Hello there"
```

### For Cloud Run:

**Get your service's URL:**
```bash
gcloud run services describe project-agora --region=us-central1 --format='value(status.url)'
```

**Visit the URL in your browser** to use the web UI, or use curl to interact with the API:
```bash
SERVICE_URL=$(gcloud run services describe project-agora --region=us-central1 --format='value(status.url)')

curl -X POST "${SERVICE_URL}/chat" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "project_agora", "query": "Hello there"}'
```