"""
Example: Iterate over Elasticsearch index.

This example demonstrates how to iterate over documents in an Elasticsearch index
using IterableData's open_iterable() function with the Elasticsearch engine.
"""

from iterable import open_iterable


def main():
    """Iterate over Elasticsearch index and print documents."""
    # Elasticsearch connection URL
    connection_url = "http://localhost:9200"
    # For authenticated clusters, use one of these options:
    # Option 1: URL-based auth: connection_url = "https://username:password@localhost:9200"
    # Option 2: API key via connect_args (see iterableargs below)
    # Option 3: Basic auth via connect_args: "connect_args": {"basic_auth": ("user", "pass")}

    # Open Elasticsearch index as iterable
    with open_iterable(
        connection_url,
        engine="elasticsearch",
        iterableargs={
            "index": "logs-2024-01",
            "body": {"query": {"match_all": {}}},
            "source_only": True,  # Return only _source fields, exclude Elasticsearch metadata
            # Uncomment to use API key authentication:
            # "connect_args": {
            #     "api_key": "your_api_key_string"  # Just the API key, or use ("id", "api_key") tuple
            # }
            # Uncomment to set timeouts:
            # "request_timeout": 30.0,  # Client-side timeout in seconds (how long to wait for response)
            # "timeout": "30s",  # Server-side timeout (passed to Elasticsearch server)
        },
    ) as source:
        print("Iterating over Elasticsearch index 'logs-2024-01'...")
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
