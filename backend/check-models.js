// Test script to verify all MongoDB models are properly defined
const path = require("path");

console.log("=== MongoDB Models Verification ===\n");

// Test 1: Check if all model files exist
console.log("1. Checking model files...");
const modelFiles = ["Book.js", "Page.js", "User.js", "SearchLog.js", "IndexTerm.js", "index.js"];
let missingFiles = [];

for (const file of modelFiles) {
  const filePath = path.join(__dirname, "src", "models", file);
  try {
    require.resolve(filePath);
    console.log(`   ✓ ${file} found`);
  } catch (err) {
    console.log(`   ✗ ${file} missing`);
    missingFiles.push(file);
  }
}

if (missingFiles.length > 0) {
  console.log(`\n❌ Missing files: ${missingFiles.join(", ")}\n`);
  process.exit(1);
}

// Test 2: Load all models
console.log("\n2. Loading models...");
try {
  const { Book, Page, User, SearchLog, IndexTerm } = require("./src/models");
  console.log("   ✓ Book model loaded");
  console.log("   ✓ Page model loaded");
  console.log("   ✓ User model loaded");
  console.log("   ✓ SearchLog model loaded");
  console.log("   ✓ IndexTerm model loaded");
} catch (err) {
  console.log(`   ✗ Failed to load models: ${err.message}`);
  process.exit(1);
}

// Test 3: Verify model schemas
console.log("\n3. Verifying schemas...");
try {
  const { Book, Page, User, SearchLog, IndexTerm } = require("./src/models");
  
  // Check Book schema
  const bookFields = Object.keys(Book.schema.paths);
  console.log(`   ✓ Book schema has ${bookFields.length} fields`);
  
  // Check Page schema
  const pageFields = Object.keys(Page.schema.paths);
  console.log(`   ✓ Page schema has ${pageFields.length} fields`);
  
  // Check User schema
  const userFields = Object.keys(User.schema.paths);
  console.log(`   ✓ User schema has ${userFields.length} fields`);
  
  // Check SearchLog schema
  const searchLogFields = Object.keys(SearchLog.schema.paths);
  console.log(`   ✓ SearchLog schema has ${searchLogFields.length} fields`);
  
  // Check IndexTerm schema
  const indexTermFields = Object.keys(IndexTerm.schema.paths);
  console.log(`   ✓ IndexTerm schema has ${indexTermFields.length} fields`);
  
} catch (err) {
  console.log(`   ✗ Schema verification failed: ${err.message}`);
  process.exit(1);
}

// Test 4: Verify model relationships
console.log("\n4. Verifying relationships...");
try {
  const { Book, Page, User, SearchLog, IndexTerm } = require("./src/models");
  
  // Check Page -> Book reference
  const pageBookRef = Page.schema.paths.bookId.options.ref;
  if (pageBookRef === "Book") {
    console.log("   ✓ Page references Book");
  } else {
    throw new Error("Page does not reference Book");
  }
  
  // Check SearchLog -> User reference
  const searchLogUserRef = SearchLog.schema.paths.userId.options.ref;
  if (searchLogUserRef === "User") {
    console.log("   ✓ SearchLog references User");
  } else {
    throw new Error("SearchLog does not reference User");
  }
  
  // Check IndexTerm postings -> Page reference
  const indexTermPageRef = IndexTerm.schema.paths.postings.schema.paths.pageId.options.ref;
  if (indexTermPageRef === "Page") {
    console.log("   ✓ IndexTerm postings reference Page");
  } else {
    throw new Error("IndexTerm postings do not reference Page");
  }
  
} catch (err) {
  console.log(`   ✗ Relationship verification failed: ${err.message}`);
  process.exit(1);
}

// Test 5: Verify indexes
console.log("\n5. Verifying indexes...");
try {
  const { Book, Page, User, SearchLog, IndexTerm } = require("./src/models");
  
  const bookIndexes = Book.schema.indexes();
  console.log(`   ✓ Book model has ${bookIndexes.length} indexes`);
  
  const pageIndexes = Page.schema.indexes();
  console.log(`   ✓ Page model has ${pageIndexes.length} indexes`);
  
  const userIndexes = User.schema.indexes();
  console.log(`   ✓ User model has ${userIndexes.length} indexes`);
  
  const searchLogIndexes = SearchLog.schema.indexes();
  console.log(`   ✓ SearchLog model has ${searchLogIndexes.length} indexes`);
  
  const indexTermIndexes = IndexTerm.schema.indexes();
  console.log(`   ✓ IndexTerm model has ${indexTermIndexes.length} indexes`);
  
} catch (err) {
  console.log(`   ✗ Index verification failed: ${err.message}`);
  process.exit(1);
}

console.log("\n=== ✅ All Model Checks Passed! ===\n");
