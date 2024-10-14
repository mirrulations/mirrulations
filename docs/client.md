# Client Documentation


## Summary
The clients are their own objects that will request work from the job queue, and perform the work by making calls to [regulations.gov]
(https://www.regulations.gov/) for data downloads, and saves the results. 

## Description 
The goal is 
that the client will request and complete work in order to download data from 
[regulations.gov](https://www.regulations.gov/).

## Attributes 
api_key: Used to authenticate requests made to the API.
client_id: An ID included in the client.env file.
path_generator: An instance of PathGenerator that returns a path for saving job results.
saver: An instance of Saver that handles saving files either to disk or Amazon S3.
redis: A connection to the Redis server for managing job states.
job_queue: A queue from which the client pulls jobs.
cache: An instance of JobStatistics for caching job statistics.

## Workflow 
Initialization: The Client is initialized with a Redis server and a job queue.
Fetching Jobs: The client attempts to fetch a job from the job queue using _get_job_from_job_queue.
Performing Jobs: Depending on the job type, the client performs the job by calling an API endpoint to request a JSON object.
Saving Results: The client saves the job results and any included attachments using the Saver class.
Updating Redis: The client updates the Redis server with job states.
