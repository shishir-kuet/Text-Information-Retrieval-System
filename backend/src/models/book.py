class BookModel:
    """Data access layer for the 'books' collection."""

    def __init__(self, db):
        self.collection = db["books"]

    def find_all(self):
        return list(self.collection.find())

    def find_by_id(self, book_id):
        return self.collection.find_one({"book_id": book_id})

    def count(self):
        return self.collection.count_documents({})

    def insert(self, book_doc):
        return self.collection.insert_one(book_doc)

    def delete_all(self):
        return self.collection.delete_many({})

    def get_domain_stats(self):
        """Return a dict of {domain: count}."""
        stats = {}
        for book in self.collection.find({}, {"domain": 1, "_id": 0}):
            domain = book.get("domain", "Unknown")
            stats[domain] = stats.get(domain, 0) + 1
        return stats
