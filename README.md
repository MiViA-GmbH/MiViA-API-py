# MiViA Python Client

Python API client for MiViA (Microstructure Analysis).

## Installation

```bash
pip install mivia
```

## Configuration

Set your API key as environment variable:

For linux:
```bash
export MIVIA_API_KEY="your-api-key"
export MIVIA_BASE_URL="https://app.mivia.ai/api"  # optional, default
export MIVIA_PROXY="http://proxy:8080"  # optional, proxy URL
```

For Windows (Powershell):
```powershell
$env:MIVIA_API_KEY = 'your-api-key'
$env:MIVIA_BASE_URL = 'https://app.mivia.ai/api'  # optional, default
$env:MIVIA_PROXY = 'http://proxy:8080'  # optional, proxy URL
```


## Usage

### Async Client

```python
import asyncio
from mivia import MiviaClient

async def main():
    async with MiviaClient() as client:
        # List models
        models = await client.list_models()
        print(f"Models: {[m.display_name for m in models]}")

        # High-level: analyze images
        jobs = await client.analyze(
            file_paths=["image1.png", "image2.png"],
            model_id=models[0].id,
            wait=True,
        )

        for job in jobs:
            print(f"Job {job.id}: {job.status}")

        # Download report
        await client.download_pdf(
            job_ids=[j.id for j in jobs],
            output_path="report.pdf",
        )

asyncio.run(main())
```

### Sync Client

```python
from mivia import SyncMiviaClient

client = SyncMiviaClient()

# List models
models = client.list_models()

# Get customizations for a model
customizations = client.get_model_customizations(models[0].id)

# Upload and analyze with customization
jobs = client.analyze(
    file_paths=["image.png"],
    model_id=models[0].id,
    customization_id=customizations[0].id if customizations else None,
)

# Download report
client.download_csv(
    job_ids=[j.id for j in jobs],
    output_path="report.zip",
)

# List all jobs for a model
from mivia import JobStatus

all_jobs = client.list_all_jobs(model_id=models[0].id)

# Filter by status
failed_jobs = client.list_all_jobs(
    model_id=models[0].id,
    status=JobStatus.FAILED,
)

# Filter by multiple statuses
active_jobs = client.list_all_jobs(
    model_id=models[0].id,
    status=[JobStatus.PENDING, JobStatus.NEW],
)
```

## CLI

```bash
# List models
mivia models

# List customizations for a model
mivia customizations MODEL_UUID

# Upload images
mivia upload image1.png image2.png

# Analyze (upload + run + wait) - supports model name or UUID
mivia analyze image.png --model "Decarburization"
mivia analyze image.png --model MODEL_UUID

# Analyze with customization (by name or UUID)
mivia analyze image.png --model "Test" --customization "Template Name"

# List available customizations for analyze
mivia analyze --model MODEL_UUID --list-customizations

# List jobs
mivia jobs list

# List jobs for specific model (by name or UUID)
mivia jobs list --model "Grain Size"

# List all jobs (fetch all pages)
mivia jobs list --model "Grain Size" --all

# Filter by status
mivia jobs list --model "Grain Size" --status FAILED --all
mivia jobs list --model "Grain Size" --status PENDING,FAILED --all

# Get recent job IDs (pipeable)
mivia jobs recent-ids --since 1h
mivia jobs recent-ids --since 2d --model "Grain Size"

# Get job details
mivia jobs get JOB_UUID

# Wait for jobs
mivia jobs wait JOB_UUID1 JOB_UUID2

# Download PDF report
mivia report pdf JOB_UUID -o report.pdf

# Download CSV report
mivia report csv JOB_UUID -o report.zip --no-images

# Show config
mivia config

# Use proxy
mivia --proxy http://proxy:8080 models
```

## Proxy Configuration

Proxy can be configured via parameter, CLI option, or environment variable.

### Library

```python
from mivia import MiviaClient, SyncMiviaClient

# Via parameter (highest priority)
async with MiviaClient(proxy="http://proxy:8080") as client:
    models = await client.list_models()

# Sync client
client = SyncMiviaClient(proxy="http://proxy:8080")
models = client.list_models()

# Via environment variable (MIVIA_PROXY)
# export MIVIA_PROXY="http://proxy:8080"
async with MiviaClient() as client:
    models = await client.list_models()
```

### CLI

```bash
# Via --proxy option
mivia --proxy http://proxy:8080 models
mivia --proxy http://proxy:8080 analyze image.png --model "Decarburization"

# Via environment variable
export MIVIA_PROXY="http://proxy:8080"
mivia models

# Verify proxy configuration
mivia --proxy http://proxy:8080 config
```

### Priority Order

1. Explicit `proxy` parameter / CLI `--proxy` option
2. `MIVIA_PROXY` environment variable
3. Standard proxy env vars (`HTTP_PROXY`, `HTTPS_PROXY`) via httpx defaults
4. No proxy (direct connection)

## API Reference

### MiviaClient

| Method | Description |
|--------|-------------|
| `upload_image(path)` | Upload single image |
| `upload_images(paths)` | Upload multiple images |
| `list_images()` | List uploaded images |
| `delete_image(id)` | Delete image |
| `list_models()` | List available models |
| `get_model_customizations(id)` | Get model customizations |
| `get_recent_job_ids(since, model_id)` | Get IDs of recently created jobs |
| `create_jobs(image_ids, model_id)` | Create computation jobs |
| `get_job(id)` | Get job details with results |
| `list_jobs()` | List jobs with pagination |
| `list_all_jobs(model_id, status)` | List all jobs with auto-pagination and filtering |
| `wait_for_job(id)` | Poll until job completes |
| `wait_for_jobs(ids)` | Wait for multiple jobs |
| `download_pdf(job_ids, path)` | Download PDF report |
| `download_csv(job_ids, path)` | Download CSV report |
| `analyze(paths, model_id)` | High-level: upload + run + wait |
