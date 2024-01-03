from services import create_user

# Example usage
create_user("new_user", "password123")

if __name__ == "__main__":
    with open("config.json") as config_file:
        config = json.load(config_file)
