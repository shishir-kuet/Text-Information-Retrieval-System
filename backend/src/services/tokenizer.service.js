const natural = require("natural");
const { removeStopwords } = require("stopword");
const logger = require("../utils/logger");

/**
 * Tokenization and text processing service for building inverted index
 */
class TokenizerService {
  constructor() {
    // Use Porter Stemmer for English
    this.stemmer = natural.PorterStemmer;
    this.tokenizer = new natural.WordTokenizer();
  }

  /**
   * Tokenize and normalize text
   * @param {string} text - Raw text to tokenize
   * @returns {Array<string>} Array of normalized tokens
   */
  tokenize(text) {
    if (!text || typeof text !== "string") {
      return [];
    }

    try {
      // 1. Convert to lowercase
      const lowerText = text.toLowerCase();

      // 2. Tokenize into words
      const tokens = this.tokenizer.tokenize(lowerText);

      if (!tokens || tokens.length === 0) {
        return [];
      }

      // 3. Filter tokens: keep only alphabetic tokens with length >= 2
      const filtered = tokens.filter(token => {
        return /^[a-z]{2,}$/.test(token);
      });

      // 4. Remove stopwords
      const withoutStopwords = removeStopwords(filtered);

      // 5. Apply stemming
      const stemmed = withoutStopwords.map(token => this.stemmer.stem(token));

      return stemmed;
    } catch (error) {
      logger.error("Tokenization error:", error);
      return [];
    }
  }

  /**
   * Calculate term frequency (TF) for a list of tokens
   * @param {Array<string>} tokens - Array of tokens
   * @returns {Object} Map of term -> frequency
   */
  calculateTermFrequency(tokens) {
    const tfMap = {};

    tokens.forEach(token => {
      if (!tfMap[token]) {
        tfMap[token] = 0;
      }
      tfMap[token]++;
    });

    return tfMap;
  }

  /**
   * Process text and return term frequencies
   * @param {string} text - Raw text
   * @returns {Object} { tokens: Array, termFrequency: Object, uniqueTerms: number }
   */
  processText(text) {
    const tokens = this.tokenize(text);
    const termFrequency = this.calculateTermFrequency(tokens);
    const uniqueTerms = Object.keys(termFrequency).length;

    return {
      tokens,
      termFrequency,
      uniqueTerms,
      totalTokens: tokens.length
    };
  }

  /**
   * Extract top N most frequent terms from text
   * @param {string} text - Raw text
   * @param {number} topN - Number of top terms to return
   * @returns {Array<{term: string, frequency: number}>}
   */
  extractTopTerms(text, topN = 10) {
    const { termFrequency } = this.processText(text);

    const sortedTerms = Object.entries(termFrequency)
      .sort((a, b) => b[1] - a[1])
      .slice(0, topN)
      .map(([term, frequency]) => ({ term, frequency }));

    return sortedTerms;
  }
}

module.exports = new TokenizerService();
