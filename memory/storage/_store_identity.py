import json
from memory.clients.supabase_conn import get_conn, release_conn

# Columns that can go directly into your identity table:
IDENTITY_COLUMNS = {
    "name",
    "birth_date",
    "primary_language",
    "gender",
    "country"
}

def _parse_key_value(text: str):
    """Extract key and value from 'key: value' format."""
    if ":" not in text:
        return None, None

    key, value = text.split(":", 1)
    key = key.strip().lower()
    value = value.strip()

    if not key or not value:
        return None, None

    return key, value


def _store_identity(content):
    """
    Store identity info:
    - If key is known identity column -> store in column
    - Else -> store inside identity_facts JSONB
    """

    if not content:
        return

    # Parse "key: value" format
    key, value = _parse_key_value(content)

    if not key or not value:
        print("Ignoring identity content (invalid key/value):", content)
        return

    conn = get_conn()

    try:
        with conn.cursor() as cur:

            # First fetch current identity_facts
            cur.execute("SELECT identity_facts FROM identity WHERE user_id = 'user-123' ;")
            row = cur.fetchone()

            current_facts = row[0] if row else {}

            # CASE 1: Key belongs to direct column
            if key in IDENTITY_COLUMNS:
                cur.execute(
                    f"""
                    INSERT INTO identity (user_id, {key})
                    VALUES ('user-123', %s)
                    ON CONFLICT (user_id) DO UPDATE SET {key} = EXCLUDED.{key};
                    """,
                    (value,)
                )
                print(f"Updated identity field: {key} -> {value}")

            else:
                current_facts = row[0] if row[0] is not None else {}
                current_facts[key] = value

                cur.execute(
                """
                    UPDATE identity
                    SET identity_facts = %s
                    WHERE user_id = 'user-123';
                    """,
                    (json.dumps(current_facts),)
                )
                print(f"Stored in identity_facts: {key} -> {value}")

            conn.commit()

    except Exception as e:
        print("Error storing identity:", e)

    finally:
        release_conn(conn)
