import os
from pinecone import Pinecone

# Global client + index holder
pinecone_client = None
pinecone_index = None

def init_pinecone():
    """
    Initialize the Pinecone client and connect to the existing index.
    """
    global pinecone_client, pinecone_index

    if pinecone_client is None:
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME")   # e.g. "orion-memory"

        if not api_key:
            raise Exception("Missing: PINECONE_API_KEY")

        if not index_name:
            raise Exception("Missing: PINECONE_INDEX_NAME")

        # Create Pinecone client
        pinecone_client = Pinecone(api_key=api_key)

        # Connect to an existing index (must already exist)
        pinecone_index = pinecone_client.Index(index_name)

        print(f"✅ Pinecone initialized → Connected to index '{index_name}'")

    return pinecone_client, pinecone_index

def get_index():
    """
    Return the active Pinecone index.
    Equivalent to get_conn() for DB.
    """
    global pinecone_index

    if pinecone_index is None:
        raise Exception("Pinecone not initialized. Call init_pinecone() first.")

    return pinecone_index