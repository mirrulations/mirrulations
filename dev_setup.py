import os
import re
import shutil

def create_env_folder():
    parent_dir = os.path.realpath(os.path.expanduser("."))
    dir_name = "env_files/"
    env_path = os.path.join(parent_dir, dir_name)
    if(os.path.exists(env_path)):
        shutil.rmtree(env_path)
    os.mkdir(env_path)

    return env_path

def get_total_client_number():
    matches = []
    with open('docker-compose.yml') as file:
        for line in file:
            match = re.findall("(client\d.env|client\d\d.env)", line)
            if len(match) == 1:
                matches += match
    return matches


def write_files(api_key, env_path, total_clients, aws_access_key, aws_secret_access_key):
    # Write client files
    for i in range(1, len(total_clients) + 1):
          with open("{}client{}.env".format(env_path, i), 'w') as file:
            file.write("API_KEY={}".format(api_key) + "\n")
            file.write("ID={}".format(i) + "\n")
            file.write("PYTHONUNBUFFERED=TRUE\n")
            file.write(f"AWS_ACCESS_KEY={aws_access_key}\n")
            file.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}")

    # Write work generator file
    with open("{}work_gen.env".format(env_path), 'w') as file:
        file.write("API_KEY={}".format(api_key) + "\n")
        file.write("PYTHONUNBUFFERED=TRUE")

    # Write dashboard file
    with open("{}dashboard.env".format(env_path), 'w') as file:
        file.write("REDIS_HOSTNAME=redis" + "\n")
        file.write("PYTHONUNBUFFERED=TRUE")
    
    # Write extractor file
    with open("{}extractor.env".format(env_path), 'w') as file:
        file.write(f"AWS_ACCESS_KEY={aws_access_key}\n")
        file.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}")
    
    # Write validator file
    with open("{}validator.env".format(env_path), 'w') as file:
        file.write("API_KEY={}".format(api_key) + "\n")
        file.write("PYTHONUNBUFFERED=TRUE")
    
    # Create data folder 
    parent_dir = os.path.realpath(os.path.expanduser("~"))
    dir_name = "data/"
    data_path = os.path.join(parent_dir, dir_name)

    if(not os.path.exists(data_path)):
        os.mkdir(data_path)


if __name__ == "__main__":

    # Get user input for API key
    api_key = input("Enter your API key from regulations.gov: ")
    aws_access_key = input("Enter your AWS Access Key: ")
    aws_secret_access_key = input("Enter your AWS Secret Access Key: ")

    env_path = create_env_folder() 
    total_clients = get_total_client_number()

    # Install all packages
    os.system("bash install_packages.sh")

    write_files(api_key, env_path, total_clients, aws_access_key, aws_secret_access_key)

            

