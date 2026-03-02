class PageModel:
    """Data access layer for the 'pages' collection."""

    def __init__(self, db):
        self.collection = db["pages"]

    def find_by_ids(self, page_ids: list) -> list:
        """Batch fetch pages by a list of page_id values."""
        return list(
            self.collection.find(
                {"page_id": {"$in": page_ids}},
                {"page_id": 1, "text_content": 1, "display_page_number": 1, "_id": 0},
            )
        )

    def find_one(self, book_id: str, page_number: int):
        return self.collection.find_one(
            {"book_id": book_id, "page_number": page_number}
        )

    def count(self) -> int:
        return self.collection.count_documents({})

    def count_with_text(self) -> int:
        return self.collection.count_documents(
            {"text_content": {"$exists": True, "$ne": ""}}
        )

    def insert_many(self, docs: list):
        return self.collection.insert_many(docs)

    def delete_all(self):
        return self.collection.delete_many({})

    def ensure_index(self):
        """Create index on page_id for fast batch lookups."""
        self.collection.create_index("page_id")
