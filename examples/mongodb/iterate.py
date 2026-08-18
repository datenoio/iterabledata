"""
Example: Iterate over MongoDB collection.

This example demonstrates how to iterate over documents in a MongoDB collection
using IterableData's open_iterable() function with the MongoDB engine.
"""

from iterable import open_iterable


def main():
    """Iterate over MongoDB collection and print documents."""
    # MongoDB connection string
    connection_string = "mongodb://localhost:27017/"

    # Open MongoDB collection as iterable
    with open_iterable(
        connection_string,
        engine="mongo",
        iterableargs={
            "database": "unicef",
            "collection": "inddata",
        },
    ) as source:
        print("Iterating over MongoDB collection 'unicef.inddata'...")
        print("-" * 60)

        count = 0
        for doc in source:
            count += 1
            print(f"Document {count}:")
            print(doc)
            print("-" * 60)

            # Limit output for demonstration (remove this in production)
            if count >= 10:
                print(f"\n... (showing first 10 documents, total available: {source.metrics.get('rows_read', 'unknown')})")
                break

        print(f"\nTotal documents processed: {count}")
        print(f"Metrics: {source.metrics}")


if __name__ == "__main__":
    main()
