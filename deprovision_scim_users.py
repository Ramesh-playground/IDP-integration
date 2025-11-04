import csv
import requests
import os
import sys

# GitHub API URL and headers
BASE_URL = "https://api.github.com/scim/v2/enterprises"
TOKEN = os.getenv("GITHUB_TOKEN")  # Token is passed as an environment variable

def get_headers():
    token = os.getenv("GITHUB_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/scim+json"
    }

def get_scim_user_id(enterprise, email):
    """Fetch the SCIM User ID for a given email, handling pagination and all emails."""
    count = 100
    start_index = 1
    headers = get_headers()
    while True:
        url = f"{BASE_URL}/{enterprise}/Users?startIndex={start_index}&count={count}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch SCIM Users: {response.status_code} {response.text}")
            sys.exit(1)
        users = response.json().get("Resources", [])
        for user in users:
            # Check all emails for a match
            for em in user.get("emails", []):
                if em.get("value") == email:
                    return user.get("id")
        if len(users) < count:
            break  # No more pages
        start_index += count
    print(f"No SCIM User ID found for email: {email}")
    return None

def delete_user(enterprise, scim_user_id):
    """Delete a user by SCIM User ID."""
    url = f"{BASE_URL}/{enterprise}/Users/{scim_user_id}"
    headers = get_headers()
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"Successfully deleted user with SCIM ID: {scim_user_id}")
    else:
        print(f"Failed to delete user: {response.status_code} {response.text}")

def main():
    """Main function to read CSV and delete users."""
    enterprise = os.getenv("ENTERPRISE_SLUG")  # Enterprise slug from environment variables
    csv_file = os.getenv("CSV_FILE", "users_to_deprovision.csv")  # CSV file path

    if not TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)
    if not enterprise:
        print("Error: ENTERPRISE_SLUG environment variable is not set.")
        sys.exit(1)

    # Read the CSV file
    try:
        with open(csv_file, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                email = row.get("email")
                if not email:
                    print("Email missing in row, skipping...")
                    continue

                print(f"Processing email: {email}")
                scim_user_id = get_scim_user_id(enterprise, email)
                if scim_user_id:
                    delete_user(enterprise, scim_user_id)

    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
