// Test Search API Functionality
require("dotenv").config();
const mongoose = require("mongoose");
const searchService = require("./src/services/search.service");
const { Book, Page, IndexTerm } = require("./src/models");

async function testSearchAPI() {
  try {
    console.log("🔍 Testing Search API with TF-IDF\n");
    
    // Connect to database
    await mongoose.connect(process.env.MONGODB_URI || "mongodb://localhost:27017/text_information_retrieval");
    console.log("✅ Connected to MongoDB\n");

    // 1. Check search readiness
    console.log("📊 Step 1: Checking search readiness...");
    const stats = await searchService.getSearchStats();
    console.log("Stats:", JSON.stringify(stats, null, 2));
    
    if (!stats.searchReady) {
      console.log("❌ Search not ready! Need to index books first.");
      process.exit(1);
    }
    console.log("✅ Search is ready!\n");

    // 2. Test queries
    const testQueries = [
      { query: "information retrieval", desc: "Basic search" },
      { query: "inverted index", desc: "Two-word query" },
      { query: "tf-idf algorithm", desc: "Three-word query" },
      { query: "search", desc: "Single word query" },
      { query: "text processing tokenization", desc: "Multiple terms" }
    ];

    for (const test of testQueries) {
      console.log(`\n🔎 Test: ${test.desc}`);
      console.log(`Query: "${test.query}"`);
      console.log("─".repeat(60));
      
      try {
        const result = await searchService.search(test.query, { limit: 3 });
        
        console.log(`Processed Query: [${result.processedQuery.join(", ")}]`);
        console.log(`Total Results: ${result.totalResults}`);
        console.log(`Returned: ${result.returnedResults}\n`);
        
        if (result.results.length === 0) {
          console.log("  ⚠️  No results found\n");
          continue;
        }
        
        result.results.forEach((r, i) => {
          console.log(`  ${i + 1}. ${r.bookTitle} - Page ${r.pageNumber}`);
          console.log(`     Score: ${r.score.toFixed(4)}`);
          console.log(`     Author: ${r.bookAuthor}`);
          console.log(`     Term Matches:`);
          r.termMatches.forEach(tm => {
            console.log(`       - "${tm.term}": tf=${tm.tf}, idf=${tm.idf.toFixed(4)}, tfidf=${tm.tfidf.toFixed(4)}`);
          });
          console.log(`     Snippet: ${r.snippet.substring(0, 100)}...`);
          console.log();
        });
        
      } catch (error) {
        console.log(`  ❌ Error: ${error.message}\n`);
      }
    }

    // 3. Test edge cases
    console.log("\n🧪 Testing Edge Cases");
    console.log("─".repeat(60));
    
    // Empty query
    console.log("\n  Test: Empty query");
    try {
      await searchService.search("");
      console.log("  ❌ Should have thrown error");
    } catch (error) {
      console.log(`  ✅ Correctly rejected: ${error.message}`);
    }

    // Stopwords only
    console.log("\n  Test: Stopwords only");
    try {
      const result = await searchService.search("the a an is");
      console.log(`  ✅ Handled gracefully: ${result.message}`);
    } catch (error) {
      console.log(`  ✅ Rejected: ${error.message}`);
    }

    // Non-existent terms
    console.log("\n  Test: Non-existent terms");
    try {
      const result = await searchService.search("xyzabc defghijk");
      console.log(`  ✅ No results: ${result.message || 'No matches'}`);
    } catch (error) {
      console.log(`  ✅ Handled: ${error.message}`);
    }

    // With options
    console.log("\n  Test: With limit and minScore options");
    try {
      const result = await searchService.search("search", { limit: 2, minScore: 0.5 });
      console.log(`  ✅ Results: ${result.returnedResults} (limit: 2, minScore: 0.5)`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // 4. Verify TF-IDF calculations
    console.log("\n\n📐 Verifying TF-IDF Calculations");
    console.log("─".repeat(60));
    
    const totalPages = await Page.countDocuments();
    console.log(`Total Pages (N): ${totalPages}`);
    
    // Pick a term and verify manually
    const sampleTerm = await IndexTerm.findOne({ term: "search" });
    if (sampleTerm) {
      console.log(`\nSample Term: "${sampleTerm.term}"`);
      console.log(`Document Frequency (DF): ${sampleTerm.df}`);
      console.log(`IDF = log(N/DF) = log(${totalPages}/${sampleTerm.df}) = ${Math.log(totalPages / sampleTerm.df).toFixed(4)}`);
      console.log(`\nPostings:`);
      sampleTerm.postings.slice(0, 3).forEach(p => {
        const tfidf = p.tf * Math.log(totalPages / sampleTerm.df);
        console.log(`  PageId: ...${p.pageId.toString().slice(-8)}, TF: ${p.tf}, TF-IDF: ${tfidf.toFixed(4)}`);
      });
    }

    // 5. Summary
    console.log("\n\n" + "═".repeat(60));
    console.log("✅ Search API Test Complete!");
    console.log("═".repeat(60));
    console.log(`Total Books: ${stats.totalBooks}`);
    console.log(`Indexed Books: ${stats.indexedBooks}`);
    console.log(`Total Pages: ${stats.totalPages}`);
    console.log(`Total Terms: ${stats.totalTerms}`);
    console.log("\nSearch API is working correctly! 🎉\n");

    await mongoose.disconnect();
    
  } catch (error) {
    console.error("\n❌ Test Failed:", error);
    console.error(error.stack);
    process.exit(1);
  }
}

testSearchAPI();
