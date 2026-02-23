const { Book, Page, IndexTerm } = require("../models");
const tokenizerService = require("./tokenizer.service");
const logger = require("../utils/logger");

/**
 * Search Service with TF-IDF Ranking
 * Implements full-text search using the inverted index
 */
class SearchService {
  /**
   * Search for documents matching a query
   * @param {string} query - Search query string
   * @param {Object} options - Search options { limit, minScore, books }
   * @returns {Promise<Object>} Search results with ranked pages
   */
  async search(query, options = {}) {
    try {
      const {
        limit = 10,
        minScore = 0.01,
        books = null // Filter by specific book IDs
      } = options;

      if (!query || query.trim().length === 0) {
        throw new Error("Query cannot be empty");
      }

      logger.info(`Searching for: "${query}"`);

      // 1. Process query: tokenize and stem
      const { tokens } = tokenizerService.processText(query);
      
      if (tokens.length === 0) {
        return {
          query: query,
          processedQuery: [],
          results: [],
          totalResults: 0,
          message: "No valid search terms after processing"
        };
      }

      logger.info(`Processed query terms: ${tokens.join(", ")}`);

      // 2. Look up terms in inverted index
      const indexTerms = await IndexTerm.find({
        term: { $in: tokens }
      });

      if (indexTerms.length === 0) {
        return {
          query: query,
          processedQuery: tokens,
          results: [],
          totalResults: 0,
          message: "No documents found for these terms"
        };
      }

      logger.info(`Found ${indexTerms.length} matching terms in index`);

      // 3. Calculate TF-IDF scores for matching pages
      const pageScores = await this.calculateTFIDF(indexTerms, tokens);

      // 4. Filter by minimum score and book IDs if specified
      let filteredScores = pageScores.filter(score => score.tfidf >= minScore);
      
      if (books && books.length > 0) {
        const bookIds = books.map(id => id.toString());
        filteredScores = filteredScores.filter(score => 
          bookIds.includes(score.bookId.toString())
        );
      }

      // 5. Sort by score (descending) and limit results
      filteredScores.sort((a, b) => b.tfidf - a.tfidf);
      const topResults = filteredScores.slice(0, limit);

      // 6. Fetch page details and generate snippets
      const results = await this.buildSearchResults(topResults, tokens);

      logger.info(`Returning ${results.length} search results`);

      return {
        query: query,
        processedQuery: tokens,
        results: results,
        totalResults: filteredScores.length,
        returnedResults: results.length
      };

    } catch (error) {
      logger.error("Search error:", error);
      throw error;
    }
  }

  /**
   * Calculate TF-IDF scores for pages
   * @param {Array} indexTerms - Terms from inverted index
   * @param {Array} queryTerms - Processed query terms
   * @returns {Promise<Array>} Array of {pageId, bookId, tfidf, termMatches}
   */
  async calculateTFIDF(indexTerms, queryTerms) {
    try {
      // Get total number of pages in the corpus
      const totalPages = await Page.countDocuments();
      
      if (totalPages === 0) {
        throw new Error("No pages in database");
      }

      logger.info(`Total pages in corpus: ${totalPages}`);

      // Map to store cumulative TF-IDF scores per page
      const pageScoresMap = new Map();

      // Process each term in the query
      for (const indexTerm of indexTerms) {
        const term = indexTerm.term;
        const df = indexTerm.df; // Document frequency
        const postings = indexTerm.postings;

        // Calculate IDF: log(N / df)
        const idf = Math.log(totalPages / df);

        logger.info(`Term "${term}": df=${df}, idf=${idf.toFixed(4)}`);

        // Calculate TF-IDF for each page containing this term
        for (const posting of postings) {
          const pageId = posting.pageId.toString();
          const tf = posting.tf; // Term frequency in this page

          // TF-IDF = TF × IDF
          const tfidf = tf * idf;

          // Accumulate score for this page
          if (!pageScoresMap.has(pageId)) {
            pageScoresMap.set(pageId, {
              pageId: posting.pageId,
              bookId: null, // Will be filled later
              tfidf: 0,
              termMatches: []
            });
          }

          const pageScore = pageScoresMap.get(pageId);
          pageScore.tfidf += tfidf;
          pageScore.termMatches.push({
            term: term,
            tf: tf,
            idf: idf,
            tfidf: tfidf
          });
        }
      }

      // Convert map to array
      const pageScores = Array.from(pageScoresMap.values());

      // Fetch book IDs for all pages (batch query)
      const pageIds = pageScores.map(score => score.pageId);
      const pages = await Page.find({ _id: { $in: pageIds } }).select("_id bookId");
      
      const pageBookMap = new Map();
      pages.forEach(page => {
        pageBookMap.set(page._id.toString(), page.bookId);
      });

      // Fill in book IDs
      pageScores.forEach(score => {
        score.bookId = pageBookMap.get(score.pageId.toString());
      });

      logger.info(`Calculated TF-IDF for ${pageScores.length} pages`);

      return pageScores;

    } catch (error) {
      logger.error("TF-IDF calculation error:", error);
      throw error;
    }
  }

  /**
   * Build final search results with page details and snippets
   * @param {Array} topResults - Top scoring pages
   * @param {Array} queryTerms - Query terms for highlighting
   * @returns {Promise<Array>} Array of complete search results
   */
  async buildSearchResults(topResults, queryTerms) {
    try {
      if (topResults.length === 0) {
        return [];
      }

      // Fetch page and book details
      const pageIds = topResults.map(result => result.pageId);
      const pages = await Page.find({ _id: { $in: pageIds } }).select("_id bookId pageNumber text tokenCount");
      
      const bookIds = [...new Set(pages.map(page => page.bookId))];
      const books = await Book.find({ _id: { $in: bookIds } }).select("_id title author");

      // Create lookup maps
      const pageMap = new Map();
      pages.forEach(page => pageMap.set(page._id.toString(), page));

      const bookMap = new Map();
      books.forEach(book => bookMap.set(book._id.toString(), book));

      // Build results with snippets
      const results = topResults.map(result => {
        const page = pageMap.get(result.pageId.toString());
        const book = bookMap.get(result.bookId.toString());

        if (!page || !book) {
          return null;
        }

        // Generate snippet with query term highlighting
        const snippet = this.generateSnippet(page.text, queryTerms);

        return {
          pageId: page._id,
          pageNumber: page.pageNumber,
          bookId: book._id,
          bookTitle: book.title,
          bookAuthor: book.author,
          score: parseFloat(result.tfidf.toFixed(4)),
          termMatches: result.termMatches.map(match => ({
            term: match.term,
            tf: match.tf,
            idf: parseFloat(match.idf.toFixed(4)),
            tfidf: parseFloat(match.tfidf.toFixed(4))
          })),
          snippet: snippet,
          tokenCount: page.tokenCount
        };
      }).filter(result => result !== null);

      return results;

    } catch (error) {
      logger.error("Build results error:", error);
      throw error;
    }
  }

  /**
   * Generate a snippet from page text with query terms highlighted
   * @param {string} text - Full page text
   * @param {Array} queryTerms - Terms to highlight
   * @param {number} maxLength - Maximum snippet length
   * @returns {string} Snippet with highlighted terms
   */
  generateSnippet(text, queryTerms, maxLength = 200) {
    if (!text || text.length === 0) {
      return "";
    }

    // Find the first occurrence of any query term
    const lowerText = text.toLowerCase();
    let firstMatchIndex = -1;

    for (const term of queryTerms) {
      const index = lowerText.indexOf(term.toLowerCase());
      if (index !== -1 && (firstMatchIndex === -1 || index < firstMatchIndex)) {
        firstMatchIndex = index;
      }
    }

    // If no term found, return beginning of text
    if (firstMatchIndex === -1) {
      return text.substring(0, maxLength) + (text.length > maxLength ? "..." : "");
    }

    // Extract snippet around the first match
    const snippetStart = Math.max(0, firstMatchIndex - 50);
    const snippetEnd = Math.min(text.length, firstMatchIndex + maxLength);
    let snippet = text.substring(snippetStart, snippetEnd);

    // Add ellipsis
    if (snippetStart > 0) {
      snippet = "..." + snippet;
    }
    if (snippetEnd < text.length) {
      snippet = snippet + "...";
    }

    // Highlight query terms (wrap in markers)
    for (const term of queryTerms) {
      const regex = new RegExp(`\\b${term}\\w*\\b`, "gi");
      snippet = snippet.replace(regex, match => `**${match}**`);
    }

    return snippet;
  }

  /**
   * Get search statistics
   * @returns {Promise<Object>} Search statistics
   */
  async getSearchStats() {
    try {
      const totalBooks = await Book.countDocuments();
      const indexedBooks = await Book.countDocuments({ status: "indexed" });
      const totalPages = await Page.countDocuments();
      const totalTerms = await IndexTerm.countDocuments();

      return {
        totalBooks,
        indexedBooks,
        totalPages,
        totalTerms,
        searchReady: indexedBooks > 0 && totalTerms > 0
      };

    } catch (error) {
      logger.error("Get search stats error:", error);
      throw error;
    }
  }
}

module.exports = new SearchService();
