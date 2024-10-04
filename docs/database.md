# Redis Database Documentation

## Database Format

We use [Redis](https://redis.io/) to store jobs as well as key values 

## Database Structure 

The Redis database is structured with the following keys: 

regulations_total_comments
num_dockets_done
num_documents_done
num_attachments_done
num_jobs_num_jobs_documents_queue_queue
num_pdf_attachment_done
num_jobs_num_jobs_dockets_queue_queue
last_job_id
jobs_in_progress
num_pdf_attachments_done
num_jobs_documents_waiting
num_jobs_comments_waiting
dockets_last_timestamp
num_jobs_num_jobs_comments_queue_queue
invalid_jobs
regulations_total_dockets
client_jobs
last_timestamp
total_num_client_ids
num_extractions_done
regulations_total_documents
mirrulations_bucket_size
num_comments_done
num_jobs_attachments_waiting
documents_last_timestamp
num_jobs_dockets_waiting
comments_last_timestamp

## Job Management

The REDIS database has three "queues", with the names:

`jobs_waiting_queue`, `jobs_in_progress`, and `jobs_done`.

The keys serve the following functions: 

jobs_waiting_queue: A list holding JSON strings representing each job.

jobs_in_progress: A hash storing jobs currently being processed.

jobs_done: A hash storing completed jobs.

The keys client_jobs and total_num_client_ids are used for sotring client information.

client_jobs: A hash mapping job IDs to client IDs.

total_num_client_ids: An integer value storing the number of clients.

## Redis Format
## `jobs_waiting_queue`

This list holds JSON strings representing each job (a job_id and a url) 

>['{"job_id" :[value], "url": [value] }',  '{"job_id" :[value], "url": [value] }', ... ]

## `jobs_in_progress`
> { [job_id] : [value] } 

## `jobs_done`
> { [job_id] : [result_value] }

## `client_jobs`
> { [job_id] : [client_id] } 


## Last timestamps

These three variables are used by the work generator to remember the last 
timestamp seen when querying regulations.gov.

* `docket_last_timestamp` - The timestamp (in UTC) of the last docket discovered
  by the work generator.
* `document_last_timestamp` - The timestamp (in UTC) of the last document 
  discovered by the work generator.
* `comment_last_timestamp` - The timestamp (in UTC) of the last comment 
  discovered by the work generator.
  
## Job IDs

The `last_job_id` variable is used by the work generator to ensure it generates
unique ids for each job.

## Client IDs

The 'last_client_id' variable is used by the work server to ensure that it
generates unique client ids.

## Job Statistics Keys 

DOCKETS_DONE: Tracks the number of completed dockets.

DOCUMENTS_DONE: Tracks the number of completed documents.

COMMENTS_DONE: Tracks the number of completed comments.

ATTACHMENTS_DONE: Tracks the number of completed attachments.

PDF_ATTACHMENTS_DONE: Tracks the number of completed PDF attachments.

EXTRACTIONS_DONE: Tracks the number of completed extractions.

MIRRULATION_BUCKET_SIZE: Stores the size of the mirrulations bucket.