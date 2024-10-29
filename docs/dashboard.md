# Dashboard Documentation

### Format & Server Overview

The main source of communication will come from a Flask server that contains two endpoints: `data` and `/`. The server will serve JSON.

The `data` endpoint will return JSON with the necessary information related to the jobs - more detailed description found below on what information the JSON would contain.

The `/` endpoint will return an HTML/CSS display of the information on the jobs.

The dashboard itself will show the number of jobs in the queue, the number of jobs in the queue of each type, the number of jobs in progress, and the number of completed jobs. It will also display the percentage of each category as well. Finally, the dashboard also displays each container currently running on the system, along with information describing its current status. This front-end will be made of HTML, CSS, and Javascript.

Currently, the server runs through port `5000`. Down the line, we hope to run through HTTPS. 

## API

For the examples below substitute `<dashboard>` with your dashboard url.
On development environments this defaults to `http://localhost`.

### Job Status

```
GET <dashboard>/data
```

Provides the counts and progress for various jobs in the json format below.

Here is the body of a sample response

```json
{
  "jobs_total": 115750,
  "mirrulations_bucket_size": 0,
  "num_attachments_done": 0,
  "num_comments_done": 0,
  "num_dockets_done": 7,
  "num_documents_done": 0,
  "num_extractions_done": 0,
  "num_jobs_comments_queued": 0,
  "num_jobs_dockets_queued": 115743,
  "num_jobs_documents_queued": 0,
  "num_jobs_done": 7,
  "num_jobs_in_progress": 0,
  "num_jobs_waiting": 115743,
  "num_pdf_attachments_done": 0,
  "regulations_total_comments": 22075373,
  "regulations_total_dockets": 253566,
  "regulations_total_documents": 1842126
}
```

### System Status

```
GET <dashboard>/devdata
```

Provides the status of currently created containers.
If a container has a health check its current health is also returned.

Here is the body of a sample response
```json
{
  "client1": {
    "status": "paused"
  },
  "dashboard": {
    "status": "running"
  },
  "extractor": {
    "status": "exited"
  },
  "nginx": {
    "status": "running"
  },
  "rabbitmq": {
    "health": "healthy",
    "status": "running"
  },
  "redis": {
    "health": "healthy",
    "status": "running"
  },
  "work_generator": {
    "status": "paused"
  }
}
```
