import json
import os
import shutil


def create_env_folder():
    parent_dir = os.path.realpath(os.path.expanduser("."))
    dir_name = "env_files/"
    env_path = os.path.join(parent_dir, dir_name)
    if os.path.exists(env_path):
        shutil.rmtree(env_path)
    os.mkdir(env_path)

    return env_path


def write_files(env_path, credentials, aws_access_key, aws_secret_access_key):
    keys_path = os.path.join(env_path, "client_keys.json")
    with open(keys_path, "w", encoding="utf-8") as file:
        json.dump(credentials, file, indent=2)
        file.write("\n")

    client_env = os.path.join(env_path, "client.env")
    with open(client_env, "w", encoding="utf-8") as file:
        file.write("CLIENT_KEYS_PATH=/config/client_keys.json\n")
        file.write("PYTHONUNBUFFERED=TRUE\n")
        file.write(f"AWS_ACCESS_KEY={aws_access_key}\n")
        file.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")

    # Work generator file (still uses API_KEY — first credential's key)
    work_gen_path = os.path.join(env_path, "work_gen.env")
    with open(work_gen_path, "w", encoding="utf-8") as file:
        file.write(f"API_KEY={credentials[0]['api_key']}\n")
        file.write("PYTHONUNBUFFERED=TRUE\n")
        file.write(f"AWS_ACCESS_KEY={aws_access_key}\n")
        file.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")

    dashboard_path = os.path.join(env_path, "dashboard.env")
    with open(dashboard_path, "w", encoding="utf-8") as file:
        file.write("REDIS_HOSTNAME=redis\n")
        file.write("PYTHONUNBUFFERED=TRUE")

    parent_dir = os.path.realpath(os.path.expanduser("~"))
    dir_name = "data/"
    data_path = os.path.join(parent_dir, dir_name)

    if not os.path.exists(data_path):
        os.mkdir(data_path)


def prompt_credentials():
    while True:
        raw = input("How many regulations.gov API keys will the client use? ")
        try:
            n = int(raw)
        except ValueError:
            print("Please enter a positive integer.")
            continue
        if n < 1:
            print("Need at least one key.")
            continue
        break

    credentials = []
    for i in range(n):
        print(f"\nKey {i + 1} of {n}:")
        key_id = input("  id (label for logs, e.g. key_a): ").strip()
        api_key = input("  api_key: ").strip()
        credentials.append({"id": key_id, "api_key": api_key})

    return credentials


if __name__ == "__main__":
    credentials = prompt_credentials()

    aws_access_key = input("Enter your AWS Access Key: ")
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ")

    env_path = create_env_folder()

    os.system("bash install_packages.sh")

    write_files(env_path, credentials, aws_access_key, aws_secret_access_key)
