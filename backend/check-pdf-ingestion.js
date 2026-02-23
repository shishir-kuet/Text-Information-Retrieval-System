// Test script to verify PDF ingestion pipeline setup
const path = require("path");
const fs = require("fs");

console.log("=== PDF Ingestion Pipeline Verification ===\n");

let errorCount = 0;

// Test 1: Check if multer config exists
console.log("1. Checking multer configuration...");
try {
  const multerPath = path.join(__dirname, "src", "config", "multer.js");
  require.resolve(multerPath);
  const upload = require("./src/config/multer");
  console.log("   ✓ Multer configuration found and loaded");
} catch (err) {
  console.log(`   ✗ Multer configuration missing or invalid: ${err.message}`);
  errorCount++;
}

// Test 2: Check if services exist
console.log("\n2. Checking services...");
try {
  const ocrService = require("./src/services/ocr.service");
  console.log("   ✓ OCR service loaded");
  
  const pdfService = require("./src/services/pdf.service");
  console.log("   ✓ PDF service loaded");
} catch (err) {
  console.log(`   ✗ Services loading failed: ${err.message}`);
  errorCount++;
}

// Test 3: Check if controller exists
console.log("\n3. Checking book controller...");
try {
  const bookController = require("./src/controllers/book.controller");
  console.log("   ✓ Book controller loaded");
  
  // Verify expected methods
  const methods = ["uploadBook", "getAllBooks", "getBookById", "deleteBook", "getBookStatus"];
  const missingMethods = methods.filter(m => typeof bookController[m] !== "function");
  
  if (missingMethods.length === 0) {
    console.log(`   ✓ All controller methods present (${methods.length})`);
  } else {
    console.log(`   ✗ Missing methods: ${missingMethods.join(", ")}`);
    errorCount++;
  }
} catch (err) {
  console.log(`   ✗ Book controller loading failed: ${err.message}`);
  errorCount++;
}

// Test 4: Check if routes exist
console.log("\n4. Checking book routes...");
try {
  const bookRoutes = require("./src/routes/book.routes");
  console.log("   ✓ Book routes loaded");
} catch (err) {
  console.log(`   ✗ Book routes loading failed: ${err.message}`);
  errorCount++;
}

// Test 5: Check if app.js includes book routes
console.log("\n5. Checking app.js integration...");
try {
  const appPath = path.join(__dirname, "src", "app.js");
  const appContent = fs.readFileSync(appPath, "utf8");
  
  if (appContent.includes("book.routes")) {
    console.log("   ✓ Book routes imported in app.js");
  } else {
    console.log("   ✗ Book routes not imported in app.js");
    errorCount++;
  }
  
  if (appContent.includes('/api/books')) {
    console.log("   ✓ Book routes registered in app.js");
  } else {
    console.log("   ✗ Book routes not registered in app.js");
    errorCount++;
  }
} catch (err) {
  console.log(`   ✗ App.js check failed: ${err.message}`);
  errorCount++;
}

// Test 6: Check required dependencies
console.log("\n6. Checking npm dependencies...");
try {
  const packageJson = require("./package.json");
  const requiredDeps = ["multer", "pdf-parse", "tesseract.js", "pdf-lib", "sharp"];
  const missingDeps = requiredDeps.filter(dep => !packageJson.dependencies[dep]);
  
  if (missingDeps.length === 0) {
    console.log(`   ✓ All required dependencies installed (${requiredDeps.length})`);
  } else {
    console.log(`   ✗ Missing dependencies: ${missingDeps.join(", ")}`);
    errorCount++;
  }
} catch (err) {
  console.log(`   ✗ Package.json check failed: ${err.message}`);
  errorCount++;
}

// Test 7: Check uploads directory
console.log("\n7. Checking uploads directory...");
const uploadsDir = path.join(__dirname, "uploads");
if (fs.existsSync(uploadsDir)) {
  console.log("   ✓ Uploads directory exists");
} else {
  console.log("   ℹ Uploads directory will be created on first upload");
}

// Summary
console.log("\n" + "=".repeat(45));
if (errorCount === 0) {
  console.log("✅ All PDF Ingestion Pipeline Checks Passed!");
} else {
  console.log(`❌ ${errorCount} check(s) failed`);
  process.exit(1);
}
console.log("=".repeat(45) + "\n");
