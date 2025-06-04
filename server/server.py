import os
from dotenv import load_dotenv
from supabase import create_client, Client
from itertools import groupby
import time

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

# Insert test legitimate customer
response = supabase.table("security_system").insert({"id": "person1", "location": "entrance/exit"}).execute()
response = supabase.table("security_system").insert({"id": "person1", "location": "checkout"}).execute()
response = supabase.table("security_system").insert({"id": "person1", "location": "entrance/exit"}).execute()

# Insert test suspicious customer
response = supabase.table("security_system").insert({"id": "person2", "location": "entrance/exit"}).execute()
response = supabase.table("security_system").insert({"id": "person2", "location": "entrance/exit"}).execute()

sus_list = []

try:
    while True:
        response = supabase.table("security_system").select("*").execute()
        table = response.data
        print("\nCurrent Data:", table)
        table.sort(key=lambda x: x["id"])
        for person, group in groupby(table, key=lambda x: x["id"]):
            group_list = list(group)
            if len(group_list) > 3:
                print(f"ERROR ({person}): Seen in cameras more than 3 times")
            else:
                if group_list[0]["location"] == "entrance/exit":
                    if len(group_list) == 2 and group_list[1]["location"] == "entrance/exit":
                        print(f"FLAGGED ({person}): Suspicious customer")
                        response = supabase.table("security_system").delete().eq("id", person).execute()
                        sus_list.append((person, group_list[0]["timestamp"], group_list[1]["timestamp"]))
                    elif len(group_list) == 3 and group_list[1]["location"] == "checkout" and group_list[2]["location"] == "entrance/exit":
                        print(f"SUCCESS ({person}): Legitimate customer")
                        response = supabase.table("security_system").delete().eq("id", person).execute()
                else:
                    print(f"ERROR ({person}): Seen in store but not at entrance/exit")

        time.sleep(5)
except KeyboardInterrupt:
    print("\nSUSPICIOUS CUSTOMERS:")
    for val in sus_list:
        print(val)