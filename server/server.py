import argparse
import os
import time
from itertools import groupby

from dotenv import load_dotenv
from supabase import Client, create_client


def insert_test_data(supabase: Client):
    # Insert test legitimate customer
    supabase.table("security_system").insert(
        {"id": "person1", "location": "entrance/exit"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person1", "location": "checkout"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person1", "location": "entrance/exit"}
    ).execute()

    # Insert test suspicious customer
    supabase.table("security_system").insert(
        {"id": "person2", "location": "entrance/exit"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person2", "location": "entrance/exit"}
    ).execute()

    print("Inserted test customers!")
    print()


def run_server(supabase: Client):
    sus_list = []

    try:
        while True:
            response = supabase.table("security_system").select("*").execute()
            table = response.data or []
            print("\nCurrent Data:", table)
            print()

            table.sort(key=lambda x: x["id"])
            for person, group in groupby(table, key=lambda x: x["id"]):
                group_list = list(group)

                if len(group_list) > 3:
                    print(f"ERROR ({person}): Seen in cameras more than 3 times")
                else:
                    first_loc = group_list[0]["location"]
                    if first_loc == "entrance/exit":
                        if (
                            len(group_list) == 2
                            and group_list[1]["location"] == "entrance/exit"
                        ):
                            print(f"FLAGGED ({person}): Suspicious customer")
                            supabase.table("security_system").delete().eq(
                                "id", person
                            ).execute()
                            sus_list.append(
                                (
                                    person,
                                    group_list[0].get("timestamp"),
                                    group_list[1].get("timestamp"),
                                )
                            )
                        elif (
                            len(group_list) == 3
                            and group_list[1]["location"] == "checkout"
                            and group_list[2]["location"] == "entrance/exit"
                        ):
                            print(f"SUCCESS ({person}): Legitimate customer")
                            supabase.table("security_system").delete().eq(
                                "id", person
                            ).execute()
                    else:
                        print(
                            f"ERROR ({person}): Seen in store but not at entrance/exit"
                        )

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nSUSPICIOUS CUSTOMERS:")
        for val in sus_list:
            print(val)


if __name__ == "__main__":
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    parser = argparse.ArgumentParser(description="Security System monitoring script")
    parser.add_argument(
        "-test",
        action="store_true",
        help="Insert test data for legitimate and suspicious customers before starting the server loop",
    )
    args = parser.parse_args()

    if args.test:
        insert_test_data(supabase)

    run_server(supabase)
