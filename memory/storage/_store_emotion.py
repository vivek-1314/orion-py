def _store_emotion(content):
        """Save ephemeral emotions with TTL"""
        # upsert_memory("emotions", content, ttl=self.emotion_ttl)
        print(f"Storing emotion memory: {content} with TTL")
