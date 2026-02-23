// Test script to verify inverted index module
const path = require("path");
const fs = require("fs");

console.log("=== Inverted Index Module Verification ===\n");

let errorCount = 0;

// Test 1: Check tokenizer service
console.log("1. Checking tokenizer service...");
try {
  const tokenizerService = require("./src/services/tokenizer.service");
  console.log("   ✓ Tokenizer service loaded");
  
  // Verify methods
  const methods = ["tokenize", "calculateTermFrequency", "processText", "extractTopTerms"];
  const missingMethods = methods.filter(m => typeof tokenizerService[m] !== "function");
  
  if (missingMethods.length === 0) {
    console.log(`   ✓ All tokenizer methods present (${methods.length})`);
  } else {
    console.log(`   ✗ Missing methods: ${missingMethods.join(", ")}`);
    errorCount++;
  }
  
  // Test tokenization
  const sampleText = "The quick brown fox jumps over the lazy dog!";
  const tokens = tokenizerService.tokenize(sampleText);
  if (tokens && tokens.length > 0) {
    console.log(`   ✓ Tokenization working (${tokens.length} tokens from sample)`);
  } else {
    console.log("   ✗ Tokenization failed");
    errorCount++;
  }
  
  // Test processText
  const result = tokenizerService.processText(sampleText);
  if (result && result.tokens && result.termFrequency && result.totalTokens) {
    console.log(`   ✓ Text processing working (${result.uniqueTerms} unique terms)`);
  } else {
    console.log("   ✗ Text processing failed");
    errorCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Tokenizer service loading failed: ${err.message}`);
  errorCount++;
}

// Test 2: Check index service
console.log("\n2. Checking index service...");
try {
  const indexService = require("./src/services/index.service");
  console.log("   ✓ Index service loaded");
  
  // Verify methods
  const methods = [
    "buildIndexForBook",
    "indexPage",
    "buildIndexForAllBooks",
    "rebuildIndex",
    "getIndexStats",
    "removeBookFromIndex"
  ];
  const missingMethods = methods.filter(m => typeof indexService[m] !== "function");
  
  if (missingMethods.length === 0) {
    console.log(`   ✓ All index service methods present (${methods.length})`);
  } else {
    console.log(`   ✗ Missing methods: ${missingMethods.join(", ")}`);
    errorCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Index service loading failed: ${err.message}`);
  errorCount++;
}

// Test 3: Check index controller
console.log("\n3. Checking index controller...");
try {
  const indexController = require("./src/controllers/index.controller");
  console.log("   ✓ Index controller loaded");
  
  // Verify methods
  const methods = [
    "buildIndexForBook",
    "buildIndexForAllBooks",
    "rebuildIndex",
    "getIndexStats",
    "removeBookFromIndex"
  ];
  const missingMethods = methods.filter(m => typeof indexController[m] !== "function");
  
  if (missingMethods.length === 0) {
    console.log(`   ✓ All controller methods present (${methods.length})`);
  } else {
    console.log(`   ✗ Missing methods: ${missingMethods.join(", ")}`);
    errorCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Index controller loading failed: ${err.message}`);
  errorCount++;
}

// Test 4: Check index routes
console.log("\n4. Checking index routes...");
try {
  const indexRoutes = require("./src/routes/index.routes");
  console.log("   ✓ Index routes loaded");
  
  // Check if it's an Express Router
  if (indexRoutes && indexRoutes.stack) {
    console.log(`   ✓ Index routes is valid Express Router`);
    console.log(`   ✓ Router has ${indexRoutes.stack.length} registered routes`);
    
    // List registered routes
    const routes = indexRoutes.stack
      .filter(r => r.route)
      .map(r => {
        const methods = Object.keys(r.route.methods).join(", ").toUpperCase();
        return `${methods} ${r.route.path}`;
      });
    
    if (routes.length > 0) {
      console.log("   Registered routes:");
      routes.forEach(route => console.log(`      • ${route}`));
    }
  } else {
    console.log("   ✗ Index routes is not a valid Express Router");
    errorCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Index routes loading failed: ${err.message}`);
  errorCount++;
}

// Test 5: Verify app.js integration
console.log("\n5. Checking app.js integration...");
try {
  const appPath = path.join(__dirname, "src", "app.js");
  const appContent = fs.readFileSync(appPath, "utf8");
  
  if (appContent.includes("index.routes")) {
    console.log("   ✓ Index routes imported in app.js");
  } else {
    console.log("   ✗ Index routes not imported in app.js");
    errorCount++;
  }
  
  if (appContent.includes('/api/index')) {
    console.log("   ✓ Index routes registered in app.js");
  } else {
    console.log("   ✗ Index routes not registered in app.js");
    errorCount++;
  }
  
  // Load app to verify no errors
  const app = require("./src/app");
  if (app) {
    console.log("   ✓ App.js loads successfully with index routes");
  }
  
} catch (err) {
  console.log(`   ✗ App.js check failed: ${err.message}`);
  errorCount++;
}

// Test 6: Check required dependencies
console.log("\n6. Checking npm dependencies...");
try {
  const packageJson = require("./package.json");
  const requiredDeps = ["natural", "stopword"];
  const missingDeps = requiredDeps.filter(dep => !packageJson.dependencies[dep]);
  
  if (missingDeps.length === 0) {
    console.log(`   ✓ All required dependencies installed (${requiredDeps.length})`);
  } else {
    console.log(`   ✗ Missing dependencies: ${missingDeps.join(", ")}`);
    errorCount++;
  }
  
  // Verify they can be loaded
  requiredDeps.forEach(dep => {
    try {
      require.resolve(dep);
      console.log(`   ✓ ${dep} can be loaded`);
    } catch {
      console.log(`   ✗ ${dep} cannot be loaded`);
      errorCount++;
    }
  });
  
} catch (err) {
  console.log(`   ✗ Package.json check failed: ${err.message}`);
  errorCount++;
}

// Test 7: Verify IndexTerm model
console.log("\n7. Checking IndexTerm model...");
try {
  const { IndexTerm } = require("./src/models");
  
  if (IndexTerm) {
    console.log("   ✓ IndexTerm model accessible");
    
    // Check schema fields
    const fields = Object.keys(IndexTerm.schema.paths);
    const requiredFields = ["term", "df", "postings"];
    const hasAllFields = requiredFields.every(field => fields.includes(field));
    
    if (hasAllFields) {
      console.log("   ✓ IndexTerm model has all required fields");
    } else {
      console.log("   ✗ IndexTerm model missing required fields");
      errorCount++;
    }
  }
  
} catch (err) {
  console.log(`   ✗ IndexTerm model check failed: ${err.message}`);
  errorCount++;
}

// Summary
console.log("\n" + "=".repeat(45));
if (errorCount === 0) {
  console.log("✅ All Inverted Index Module Checks Passed!");
  console.log("\nℹ️  Module is ready for testing");
} else {
  console.log(`❌ ${errorCount} check(s) failed`);
  process.exit(1);
}
console.log("=".repeat(45) + "\n");
