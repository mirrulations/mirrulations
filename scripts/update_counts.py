import argparse
import json
import redis
import sys

def list_current_values(r):
    keys = [
        "num_dockets_done",
        "num_documents_done",
        "num_comments_done",
        "dockets_last_timestamp",
        "documents_last_timestamp",
        "comments_last_timestamp"
    ]
    print("Current Redis Key Values:")
    print("-" * 50)
    for key in keys:
        value = r.get(key)
        value = value.decode('utf-8') if value else 'None'
        print(f"{key}: {value}")
    print("-" * 50)

def update_values(r, data):
    # Extract values from JSON data
    num_dockets_done = data.get("dockets", {}).get("downloaded", 0)
    num_documents_done = data.get("documents", {}).get("downloaded", 0)
    num_comments_done = data.get("comments", {}).get("downloaded", 0)
    stop_timestamp = data.get("stop_timestamp", "")
    
    # Mapping from Redis keys to values
    key_value_pairs = {
        "num_dockets_done": num_dockets_done,
        "num_documents_done": num_documents_done,
        "num_comments_done": num_comments_done,
        "dockets_last_timestamp": stop_timestamp,
        "documents_last_timestamp": stop_timestamp,
        "comments_last_timestamp": stop_timestamp
    }

    # Display current and new values
    print("Current and New Values:")
    print("-" * 50)
    for key, new_value in key_value_pairs.items():
        current_value = r.get(key)
        current_value = current_value.decode('utf-8') if current_value else 'None'
        print(f"Key: {key}")
        print(f"Current Value: {current_value}")
        print(f"New Value: {new_value}")
        print("-" * 50)

    # Confirm before updating
    confirm = input("Do you want to update these keys with the new values? (yes/no): ").strip().lower()
    if confirm == 'yes':
        for key, new_value in key_value_pairs.items():
            r.set(key, new_value)
        print("Keys have been updated successfully.")
    else:
        print("No changes have been made.")

def main():
    parser = argparse.ArgumentParser(description="Redis Key Updater")
    parser.add_argument('-i', '--input', help='Path to the JSON file')
    args = parser.parse_args()

    # Connect to Redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
        sys.exit(1)

    if args.input:
        # Load JSON data from the provided file
        try:
            with open(args.input, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            sys.exit(1)
        update_values(r, data)
    else:
        # List current values
        list_current_values(r)

if __name__ == "__main__":
    main()
