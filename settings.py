import os
from dotenv import load_dotenv


def load_environment(env_type):
    """
    Load the appropriate environment variables from a .env file
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_dir = ".envs"
    env_file = f"{env_dir}/{env_type}/.flask"
    env_path = os.path.join(base_dir, env_file)
    load_dotenv(env_path)


# Determine the environment to use ('.local' or '.production')
ENVIRONMENT_TYPE = os.getenv("ENVIRONMENT_TYPE", "local")

# Load the environment variables from the respective file
load_environment(ENVIRONMENT_TYPE)
