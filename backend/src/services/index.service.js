const { Book, Page, IndexTerm } = require("../models");
const tokenizerService = require("./tokenizer.service");
const logger = require("../utils/logger");

/**
 * Inverted Index Builder Service
 * Builds and maintains the inverted index for full-text search
 */
class IndexService {
  /**
   * Build inverted index for a specific book
   * @param {string} bookId - MongoDB ObjectId of the book
   * @returns {Promise<Object>} Index statistics
   */
  async buildIndexForBook(bookId) {
    try {
      // 1. Verify book exists and is processed
      const book = await Book.findById(bookId);
      if (!book) {
        throw new Error("Book not found");
      }

      if (book.status !== "processed") {
        throw new Error(`Book status is '${book.status}'. Must be 'processed' to build index.`);
      }

      logger.info(`Building index for book: ${book.title} (ID: ${bookId})`);

      // Update book status to indexing
      book.status = "indexing";
      await book.save();

      // 2. Get all pages for this book
      const pages = await Page.find({ bookId: bookId }).sort({ pageNumber: 1 });
      
      if (pages.length === 0) {
        throw new Error("No pages found for this book");
      }

      logger.info(`Found ${pages.length} pages to index`);

      // 3. Build index from pages
      const indexStats = {
        bookId: bookId,
        bookTitle: book.title,
        totalPages: pages.length,
        termsAdded: 0,
        termsUpdated: 0,
        totalTokens: 0,
        uniqueTerms: new Set()
      };

      for (const page of pages) {
        const pageStats = await this.indexPage(page);
        indexStats.totalTokens += pageStats.totalTokens;
        indexStats.termsAdded += pageStats.termsAdded;
        indexStats.termsUpdated += pageStats.termsUpdated;
        pageStats.uniqueTerms.forEach(term => indexStats.uniqueTerms.add(term));
      }

      // 4. Update book status to indexed
      book.status = "indexed";
      await book.save();

      indexStats.uniqueTerms = indexStats.uniqueTerms.size;

      logger.info(`Index built for book: ${book.title}. Stats:`, indexStats);

      return indexStats;
    } catch (error) {
      logger.error("Error building index for book:", error);
      
      // Update book status to failed if it exists
      try {
        const book = await Book.findById(bookId);
        if (book) {
          book.status = "failed";
          book.ocrError = `Index building failed: ${error.message}`;
          await book.save();
        }
      } catch (updateError) {
        logger.error("Failed to update book status:", updateError);
      }

      throw error;
    }
  }

  /**
   * Index a single page
   * @param {Object} page - Page document from MongoDB
   * @returns {Promise<Object>} Page indexing statistics
   */
  async indexPage(page) {
    try {
      // 1. Tokenize page text
      const { termFrequency, totalTokens } = tokenizerService.processText(page.text);

      const stats = {
        pageId: page._id,
        pageNumber: page.pageNumber,
        totalTokens: totalTokens,
        termsAdded: 0,
        termsUpdated: 0,
        uniqueTerms: new Set()
      };

      // 2. Update inverted index for each term
      for (const [term, tf] of Object.entries(termFrequency)) {
        stats.uniqueTerms.add(term);

        // Find or create index term
        let indexTerm = await IndexTerm.findOne({ term: term });

        if (indexTerm) {
          // Term exists - check if this page is already in postings
          const existingPosting = indexTerm.postings.find(
            p => p.pageId.toString() === page._id.toString()
          );

          if (existingPosting) {
            // Update existing posting
            existingPosting.tf = tf;
          } else {
            // Add new posting for this page
            indexTerm.postings.push({
              pageId: page._id,
              tf: tf
            });
            indexTerm.df = indexTerm.postings.length;
          }

          await indexTerm.save();
          stats.termsUpdated++;
        } else {
          // Create new index term
          indexTerm = await IndexTerm.create({
            term: term,
            df: 1,
            postings: [
              {
                pageId: page._id,
                tf: tf
              }
            ]
          });
          stats.termsAdded++;
        }
      }

      return stats;
    } catch (error) {
      logger.error(`Error indexing page ${page.pageNumber}:`, error);
      throw error;
    }
  }

  /**
   * Build index for all processed books
   * @returns {Promise<Object>} Overall indexing statistics
   */
  async buildIndexForAllBooks() {
    try {
      logger.info("Building index for all processed books...");

      // Find all books with status 'processed'
      const books = await Book.find({ status: "processed" });

      if (books.length === 0) {
        logger.info("No processed books found to index");
        return {
          message: "No processed books found",
          booksIndexed: 0
        };
      }

      logger.info(`Found ${books.length} processed books to index`);

      const overallStats = {
        booksIndexed: 0,
        totalPages: 0,
        totalTokens: 0,
        totalUniqueTerms: 0,
        termsAdded: 0,
        termsUpdated: 0,
        books: []
      };

      for (const book of books) {
        try {
          const bookStats = await this.buildIndexForBook(book._id.toString());
          overallStats.booksIndexed++;
          overallStats.totalPages += bookStats.totalPages;
          overallStats.totalTokens += bookStats.totalTokens;
          overallStats.termsAdded += bookStats.termsAdded;
          overallStats.termsUpdated += bookStats.termsUpdated;
          overallStats.books.push({
            bookId: bookStats.bookId,
            title: bookStats.bookTitle,
            pages: bookStats.totalPages,
            tokens: bookStats.totalTokens
          });
        } catch (error) {
          logger.error(`Failed to index book ${book.title}:`, error.message);
          // Continue with next book
        }
      }

      // Count total unique terms in index
      const uniqueTermsCount = await IndexTerm.countDocuments();
      overallStats.totalUniqueTerms = uniqueTermsCount;

      logger.info("Indexing complete. Overall stats:", overallStats);

      return overallStats;
    } catch (error) {
      logger.error("Error building index for all books:", error);
      throw error;
    }
  }

  /**
   * Rebuild entire index (clear and rebuild)
   * @returns {Promise<Object>} Rebuild statistics
   */
  async rebuildIndex() {
    try {
      logger.info("Rebuilding entire index...");

      // 1. Clear existing index
      const deletedCount = await IndexTerm.deleteMany({});
      logger.info(`Cleared ${deletedCount.deletedCount} existing index terms`);

      // 2. Reset all book statuses from 'indexed' to 'processed'
      await Book.updateMany(
        { status: "indexed" },
        { status: "processed" }
      );

      // 3. Build index for all books
      const stats = await this.buildIndexForAllBooks();

      return {
        message: "Index rebuilt successfully",
        clearedTerms: deletedCount.deletedCount,
        ...stats
      };
    } catch (error) {
      logger.error("Error rebuilding index:", error);
      throw error;
    }
  }

  /**
   * Get index statistics
   * @returns {Promise<Object>} Index statistics
   */
  async getIndexStats() {
    try {
      const totalTerms = await IndexTerm.countDocuments();
      const indexedBooks = await Book.countDocuments({ status: "indexed" });
      const totalBooks = await Book.countDocuments();
      const totalPages = await Page.countDocuments();

      // Get sample of most common terms
      const topTerms = await IndexTerm.find()
        .sort({ df: -1 })
        .limit(10)
        .select("term df");

      return {
        totalTerms,
        indexedBooks,
        totalBooks,
        totalPages,
        indexCoverage: totalBooks > 0 ? ((indexedBooks / totalBooks) * 100).toFixed(2) + "%" : "0%",
        topTermsByDocFrequency: topTerms
      };
    } catch (error) {
      logger.error("Error getting index stats:", error);
      throw error;
    }
  }

  /**
   * Remove index entries for a specific book
   * @param {string} bookId - MongoDB ObjectId of the book
   */
  async removeBookFromIndex(bookId) {
    try {
      logger.info(`Removing book ${bookId} from index...`);

      // Get all pages for this book
      const pages = await Page.find({ bookId: bookId }).select("_id");
      const pageIds = pages.map(p => p._id.toString());

      if (pageIds.length === 0) {
        logger.info("No pages found for this book");
        return { removedTerms: 0 };
      }

      // Find all index terms that reference these pages
      const indexTerms = await IndexTerm.find({
        "postings.pageId": { $in: pageIds }
      });

      let removedTerms = 0;

      for (const indexTerm of indexTerms) {
        // Remove postings for this book's pages
        indexTerm.postings = indexTerm.postings.filter(
          p => !pageIds.includes(p.pageId.toString())
        );

        if (indexTerm.postings.length === 0) {
          // No more postings - delete the term
          await IndexTerm.deleteOne({ _id: indexTerm._id });
          removedTerms++;
        } else {
          // Update df and save
          indexTerm.df = indexTerm.postings.length;
          await indexTerm.save();
        }
      }

      logger.info(`Removed ${removedTerms} terms from index for book ${bookId}`);

      return { removedTerms };
    } catch (error) {
      logger.error("Error removing book from index:", error);
      throw error;
    }
  }
}

module.exports = new IndexService();
