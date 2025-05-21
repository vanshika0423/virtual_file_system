from metadata.db import fetch_all_metadata

def main():
    rows = fetch_all_metadata()
    if not rows:
        print("No metadata rows found in database.")
    else:
        print(f"Found {len(rows)} metadata rows:")
        for row in rows:
            print(row)

if __name__ == "__main__":
    main()
