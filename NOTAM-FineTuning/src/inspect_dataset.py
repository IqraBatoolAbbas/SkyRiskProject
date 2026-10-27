
from datasets import load_dataset

DATASET_ID = "DEEL-AI/NOTAM"


def main():
    print(f"Loading dataset: {DATASET_ID}")

    dataset = load_dataset(DATASET_ID)

    print("\nAvailable splits:")
    for split_name, split_data in dataset.items():
        print(f"\nSplit: {split_name}")
        print(f"Rows: {len(split_data)}")
        print(f"Columns: {split_data.column_names}")

        print("\nFeatures:")
        print(split_data.features)

        print("\nFirst 3 records:")
        for row in split_data.select(range(min(3, len(split_data)))):
            print(row)


if __name__ == "__main__":
    main()
