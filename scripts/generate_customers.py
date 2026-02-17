import csv
import random
from faker import Faker
import os

def generate_customer_csv(
    output_path,
    num_rows=1000,
    seed=42,
    minor_probability=0.1,
    restricted_region_probability=0.05
):
    """
    Generates a synthetic customer dataset for compliance testing.
    Columns: Name, Email, Age, Country, Subscription_Type
    """
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = ["Name", "Email", "Age", "Country", "Subscription_Type"]

    countries = ["USA", "UK", "Canada", "Germany", "France", "Japan", "Australia"]
    subscription_types = ["Free", "Pro", "Enterprise"]

    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        emails = set()

        while len(emails) < num_rows:
            # Name
            name = fake.name()

            # Email (ensure uniqueness)
            email = fake.unique.email()
            emails.add(email)

            # Age logic
            if random.random() < minor_probability:
                age = random.randint(13, 17)
            else:
                age = random.randint(18, 80)

            # Country logic
            if random.random() < restricted_region_probability:
                country = "GDPR_Restricted_Zone"
            else:
                country = random.choice(countries)

            sub_type = random.choice(subscription_types)

            writer.writerow([name, email, age, country, sub_type])

if __name__ == "__main__":
    # Default generation for the project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(base_dir, "data", "customers.csv")
    print(f"Generating synthetic customer data: {target}")
    generate_customer_csv(target)
    print("Done.")
