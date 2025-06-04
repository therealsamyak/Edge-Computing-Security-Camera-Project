import argparse
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

from dotenv import load_dotenv
from supabase import Client, create_client


def insert_test_data(supabase: Client):
    # Delete any leftover data
    supabase.table("security_system").delete().neq(
        "id", None
    ).execute()

    # Insert test legitimate customer
    supabase.table("security_system").insert(
        {"id": "person1", "location": "entrance/exit"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person1", "location": "entrance/exit"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person1", "location": "checkout"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person1", "location": "checkout"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person1", "location": "entrance/exit"}
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
    time.sleep(15)
    supabase.table("security_system").insert(
        {"id": "person2", "location": "entrance/exit"}
    ).execute()
    supabase.table("security_system").insert(
        {"id": "person2", "location": "entrance/exit"}
    ).execute()

    print("\nInserted test customers!\n")


def group_by_time_proximity(group_list, time_key="timestamp", threshold_seconds=15):
    groups = []
    stored_entry = None

    for entry in group_list:
        entry_time = datetime.fromisoformat(entry.get(time_key))
        
        if not stored_entry:
            stored_entry = entry
        else:
            prev_time = datetime.fromisoformat(stored_entry.get(time_key))
            if (stored_entry.get("location") != entry.get("location")) or (entry_time - prev_time) > timedelta(seconds=threshold_seconds):
                groups.append(stored_entry)
                stored_entry = entry

    if stored_entry:
        groups.append(stored_entry)
    
    return groups


def run_server(supabase: Client):
    sus_list = []

    try:
        while True:
            response = supabase.table("security_system").select("*").execute()
            table = response.data or []
            print("\nCurrent Data:", table)
            print()

            grouped = defaultdict(list)
            for row in table:
                if "id" in row:
                    grouped[row["id"]].append(row)
            for person, group_list in grouped.items():
                group_list = group_by_time_proximity(group_list)
                first_loc = group_list[0].get("location")
                if first_loc == "entrance/exit":
                    checkout_loc = any(element.get("location") == "checkout" for element in group_list)
                    if (
                        not checkout_loc
                        and group_list[-1].get("location") == "entrance/exit"
                        and len(group_list) > 1
                    ):
                        print(f"FLAGGED ({person}): Suspicious customer")
                        supabase.table("security_system").delete().eq(
                            "id", person
                        ).execute()
                        sus_list.append(
                            (
                                person,
                                group_list[0].get("timestamp"),
                                group_list[-1].get("timestamp"),
                            )
                        )
                    elif (
                        checkout_loc
                        and group_list[-1].get("location") == "entrance/exit"
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