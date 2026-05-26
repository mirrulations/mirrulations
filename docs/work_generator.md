# Work Generator Documentation

## Summary

The work generator has three functions:

1. Creation of download jobs
2. Updating the stored total docket, document, and comment counts from Regulations.gov
3. Updating the stored current size of the AWS S3 Bucket

To accomplish its functions, the work generator externally interacts with Regulations.gov and AWS. Internally, the work generator updates values in **Redis** and the **RabbitMQ** job queue.

## Details

Once started the work generator attempts to perform its functions every 6 hours.

### Creating Download Jobs

The work generator iterates over dockets, documents, and comments modified on Regulations.gov since its last run, and creates download jobs for them in the job queue. A download job includes at least **`job_id`**, **`url`**, and **`job_type`** (see [database.md](database.md)). Jobs are added to the queue in batches of up to 250, with a minimum of 3.6 seconds between each batch. The **client** consumes those jobs and persists results under **`raw-data/`** as described in **[structure.md](structure.md)**.

### Docket, Document, and Comment Counts

Before creating any download jobs, the work generator queries Regulations.gov via it's API for total counts of dockets, documents, and comments. It stores these counts within the database.

### AWS S3 Bucket Size

Before creating any download jobs, the work generator attempts to query the AWS S3 bucket where dockets, documents, and comments will be downloaded to. It stores this value within the database.
