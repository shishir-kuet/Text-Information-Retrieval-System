// Comprehensive test for PDF ingestion pipeline
const path = require("path");
const fs = require("fs");

console.log("=== PDF Ingestion Pipeline - Comprehensive Test ===\n");

let passCount = 0;
let failCount = 0;

// Test 1: Load and verify all services
console.log("1. Testing Services...");
try {
  const ocrService = require("./src/services/ocr.service");
  const pdfService = require("./src/services/pdf.service");
  
  // Check OCR service methods
  if (typeof ocrService.initialize === "function") {
    console.log("   ✓ OCR service has initialize method");
    passCount++;
  } else {
    console.log("   ✗ OCR service missing initialize method");
    failCount++;
  }
  
  if (typeof ocrService.extractText === "function") {
    console.log("   ✓ OCR service has extractText method");
    passCount++;
  } else {
    console.log("   ✗ OCR service missing extractText method");
    failCount++;
  }
  
  // Check PDF service methods
  const pdfMethods = ["processPDF", "processPage", "getBookWithPages", "getAllBooks", "deleteBook"];
  pdfMethods.forEach(method => {
    if (typeof pdfService[method] === "function") {
      console.log(`   ✓ PDF service has ${method} method`);
      passCount++;
    } else {
      console.log(`   ✗ PDF service missing ${method} method`);
      failCount++;
    }
  });
  
} catch (err) {
  console.log(`   ✗ Service loading failed: ${err.message}`);
  failCount++;
}

// Test 2: Load and verify controller
console.log("\n2. Testing Controller...");
try {
  const bookController = require("./src/controllers/book.controller");
  
  const controllerMethods = ["uploadBook", "getAllBooks", "getBookById", "deleteBook", "getBookStatus"];
  controllerMethods.forEach(method => {
    if (typeof bookController[method] === "function") {
      console.log(`   ✓ Controller has ${method} method`);
      passCount++;
    } else {
      console.log(`   ✗ Controller missing ${method} method`);
      failCount++;
    }
  });
  
} catch (err) {
  console.log(`   ✗ Controller loading failed: ${err.message}`);
  failCount++;
}

// Test 3: Load and verify routes
console.log("\n3. Testing Routes...");
try {
  const bookRoutes = require("./src/routes/book.routes");
  
  // Check if it's an Express Router
  if (bookRoutes && bookRoutes.stack) {
    console.log(`   ✓ Book routes is valid Express Router`);
    console.log(`   ✓ Router has ${bookRoutes.stack.length} registered routes`);
    passCount += 2;
    
    // List registered routes
    const routes = bookRoutes.stack
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
    console.log("   ✗ Book routes is not a valid Express Router");
    failCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Routes loading failed: ${err.message}`);
  failCount++;
}

// Test 4: Verify multer configuration
console.log("\n4. Testing Multer Configuration...");
try {
  const upload = require("./src/config/multer");
  
  if (upload && typeof upload.single === "function") {
    console.log("   ✓ Multer upload instance created");
    passCount++;
  } else {
    console.log("   ✗ Invalid multer configuration");
    failCount++;
  }
  
  // Check uploads directory
  const uploadsDir = path.join(__dirname, "uploads");
  if (fs.existsSync(uploadsDir)) {
    console.log("   ✓ Uploads directory exists");
    passCount++;
  } else {
    console.log("   ℹ Uploads directory will be created on first upload");
    passCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Multer configuration failed: ${err.message}`);
  failCount++;
}

// Test 5: Verify app.js integration
console.log("\n5. Testing App.js Integration...");
try {
  const app = require("./src/app");
  
  if (app) {
    console.log("   ✓ App.js loads successfully");
    passCount++;
  }
  
  // Check if app has routes registered
  if (app._router) {
    const routes = [];
    app._router.stack.forEach(middleware => {
      if (middleware.route) {
        const methods = Object.keys(middleware.route.methods).join(", ").toUpperCase();
        routes.push(`${methods} ${middleware.route.path}`);
      } else if (middleware.name === "router") {
        const routerPath = middleware.regexp.toString();
        if (routerPath.includes("books")) {
          console.log("   ✓ Book routes registered in app");
          passCount++;
        }
        if (routerPath.includes("health")) {
          console.log("   ✓ Health routes registered in app");
          passCount++;
        }
      }
    });
  }
  
} catch (err) {
  console.log(`   ✗ App integration failed: ${err.message}`);
  failCount++;
}

// Test 6: Verify models are accessible
console.log("\n6. Testing Database Models...");
try {
  const { Book, Page } = require("./src/models");
  
  if (Book) {
    console.log("   ✓ Book model accessible");
    passCount++;
    
    // Check Book schema fields
    const bookFields = Object.keys(Book.schema.paths);
    const requiredBookFields = ["title", "fileName", "status"];
    const hasAllFields = requiredBookFields.every(field => bookFields.includes(field));
    
    if (hasAllFields) {
      console.log("   ✓ Book model has all required fields");
      passCount++;
    } else {
      console.log("   ✗ Book model missing required fields");
      failCount++;
    }
  }
  
  if (Page) {
    console.log("   ✓ Page model accessible");
    passCount++;
    
    // Check Page schema fields
    const pageFields = Object.keys(Page.schema.paths);
    const requiredPageFields = ["bookId", "pageNumber", "text"];
    const hasAllFields = requiredPageFields.every(field => pageFields.includes(field));
    
    if (hasAllFields) {
      console.log("   ✓ Page model has all required fields");
      passCount++;
    } else {
      console.log("   ✗ Page model missing required fields");
      failCount++;
    }
  }
  
} catch (err) {
  console.log(`   ✗ Models loading failed: ${err.message}`);
  failCount++;
}

// Test 7: Check dependencies
console.log("\n7. Testing Dependencies...");
try {
  const requiredDeps = [
    "multer",
    "pdf-parse",
    "tesseract.js",
    "pdf-lib",
    "sharp"
  ];
  
  requiredDeps.forEach(dep => {
    try {
      require.resolve(dep);
      console.log(`   ✓ ${dep} installed`);
      passCount++;
    } catch {
      console.log(`   ✗ ${dep} not installed`);
      failCount++;
    }
  });
  
} catch (err) {
  console.log(`   ✗ Dependency check failed: ${err.message}`);
  failCount++;
}

// Test 8: Verify error middleware
console.log("\n8. Testing Error Middleware...");
try {
  const { notFoundHandler, errorHandler } = require("./src/middlewares/error.middleware");
  
  if (typeof notFoundHandler === "function") {
    console.log("   ✓ notFoundHandler exists");
    passCount++;
  } else {
    console.log("   ✗ notFoundHandler missing");
    failCount++;
  }
  
  if (typeof errorHandler === "function") {
    console.log("   ✓ errorHandler exists");
    passCount++;
  } else {
    console.log("   ✗ errorHandler missing");
    failCount++;
  }
  
} catch (err) {
  console.log(`   ✗ Error middleware check failed: ${err.message}`);
  failCount++;
}

// Summary
console.log("\n" + "=".repeat(50));
console.log(`Total Tests: ${passCount + failCount}`);
console.log(`Passed: ${passCount} ✓`);
console.log(`Failed: ${failCount} ✗`);

if (failCount === 0) {
  console.log("\n✅ All PDF Ingestion Tests Passed!");
  console.log("\nℹ️  Runtime Testing Notes:");
  console.log("   • MongoDB must be running for actual PDF uploads");
  console.log("   • Start server: npm run dev");
  console.log("   • Test upload: POST http://localhost:5000/api/books/upload");
  console.log("   • Use Postman or cURL with multipart/form-data");
  process.exit(0);
} else {
  console.log("\n❌ Some tests failed. Please fix the issues above.");
  process.exit(1);
}
console.log("=".repeat(50) + "\n");
