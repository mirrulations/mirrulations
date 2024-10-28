# Client Documentation

## Summary

Clients are components of the Mirrulations system responsible for downloading data from Regulations.gov. Unless stopped a client continues to attempt the following steps:

1. Get work from the job queue
2. Perform the job by downloading data from Regulations.gov
3. Save downloaded regulation data

To accomplish their task each client interacts externally with Regulations.gov and AWS S3. Internally, each client interacts with the database (Redis) and queue (RabbitMQ).

## Details

Every 3.6 seconds a client attempts to get a job, perform its jobs, and save the resulting data.
Download jobs have three fields: `job_id`, `url`, and `job_type`.

### Getting Work

A client gets work by removing a job from the queue and updating it's current job in the database.

If no work is available at the current time the client waits for 3.6 seconds before attempting again.

### Data Download

After receiving a job, a client attempts to download the remote resource pointed to by its url. If the `job_type` is a comment, any attachments are also downloaded. The client updates the database after the job is completed.

If an unrecoverable error occurs while during download, the client marks the job as an invalid job in the database. Invalid jobs will not be retried by other clients.

### Saving Data

After downloading data it is saved. By default data is saved to disk and to the `mirrulations` AWS S3 bucket.
