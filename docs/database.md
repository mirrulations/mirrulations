# Redis Database Documentation

## Database Format

We use [Redis](https://redis.io/) to store jobs as well as key values that must
be remembered.

## Job Management

The REDIS database has three "queues", with the names:

`jobs_waiting_queue`, `jobs_in_progress`, and `jobs_done`.

`jobs_waiting_queue` is a list, while 'jobs_in_progress' and 'jobs_done' are hashes.
Each stores jobs for clients to process.

Keys will be integers, the job ids of the jobs.
These keys will be mapped to integers, the values to be processed.

Additionally, the database has an integer value storing the number of clients:
`total_num_client_ids`.

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