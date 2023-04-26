# Extraction Queue

## Purpose
- Replace current slow text extraction process (`os.walk`)
- Allow the ability to parallelize the extraction process

## What has been done?

- Created a new class called `ExtractionQueue` that will handle the extraction process located at `mirrulations-core/src/mirrcore/extraction_queue.py`

#### Extraction Queue
- This class's implementation is similar to that of `JobQueue`
- To implement, each `client` should have an `ExtractionQueue` instance and can append the path to an attachment to the queue. It will later be popped off by one of the extraction workers.
- Each extraction process will also have an instance of the `ExtractionQueue` and attempt to pop an attachment's path off the queue and extract the text from it.
- If the queue is empty, the process will sleep for `n` seconds and try again.
- Once this process is implemented, a script must be run over the all the data to add any `non-extracted` attachment paths to the queue to be processed.
