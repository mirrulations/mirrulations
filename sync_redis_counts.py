"""
Script that will update the num_[job_type]_count numbers in redis based off the mirrulations data
found in the data disk folder

Using redis variables to store counts can cause the number to go stale (out of sync with actual data
stored on disk). This script will help in keeping Redis as accurate as possible of corpus data status

TODO: extracted texts
"""
import os
import redis

DOCKETS_DONE = "num_dockets_done"
DOCUMENTS_DONE = "num_documents_done"
COMMENTS_DONE = "num_comments_done"
ATTACHMENTS_DONE = 'num_attachments_done'

redis_server = redis.Redis(port=6379)


def set_redis_num_done_counts(key, total):
    """
    sets the redis key to its total count
    """
    redis_server.set(key, total)


def get_dockets_count(data_dir):
    """
    returns the total number of dockets found across all agencies subdirectories
    """
    total = 0

    for agency_dir in os.listdir(data_dir):
        agency_path = os.path.join(data_dir, agency_dir)
        total += len(os.listdir(agency_path))
    return total           


def get_documents_comments_count(agency_dir, docket_dir):
    """
    gets the number of documents and comments found within the text- subdirectories of a docket
    """
    counts = {'documents': 0, 'comments': 0}

    for subdir in counts:
        subdir_path = os.path.join(agency_dir, docket_dir, subdir)
        if os.path.isdir(subdir_path):
            counts[subdir] = len(os.listdir(subdir_path))

    return counts['documents'], counts['comments']


def get_attachments_count(agency_dir, docket_dir):
    """
    gets the number of attachments found within the binary- subdirectories of a docket
    """
    attachments_total = 0
    comments_attachments_dir = os.path.join(agency_dir, docket_dir, 'comments_attachments')
    if os.path.isdir(comments_attachments_dir):
        attachments_total += len(os.listdir(comments_attachments_dir))

    return attachments_total


def main():
    counts = {
        DOCKETS_DONE: 0,
        DOCUMENTS_DONE: 0,
        COMMENTS_DONE: 0,
        ATTACHMENTS_DONE: 0
    }

    if input("Are you sure you want to update the redis counts. press y for yes: ") == 'y':
        home_dir = os.path.expanduser("~")
        data_dir = os.path.join(home_dir, "data", "data")

        counts[DOCKETS_DONE] += get_dockets_count(data_dir) # change to /data

        for agency_dir, dirs, _ in os.walk(data_dir):
            for docket_dir in dirs:
                if docket_dir.startswith('text-'):
                    # only search for documents, comments in the text directories
                    documents, comments = get_documents_comments_count(agency_dir, docket_dir)
                    counts[DOCUMENTS_DONE] += documents
                    counts[COMMENTS_DONE] += comments
                elif docket_dir.startswith('binary-'):
                    # only seacrch for attachments in the binary directories
                    counts[ATTACHMENTS_DONE] += get_attachments_count(agency_dir, docket_dir)

        print("dockets:", counts[DOCKETS_DONE])
        print("documents:", counts[DOCUMENTS_DONE])
        print("comments:", counts[COMMENTS_DONE])
        print("attachments:", counts[ATTACHMENTS_DONE])

        for key, count in counts.items():
            set_redis_num_done_counts(key, count)

    else:
        print("exited")


if __name__ == '__main__':
    main()
