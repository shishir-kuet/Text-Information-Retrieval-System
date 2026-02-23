// Check pages for a book
require("dotenv").config();
const mongoose = require("mongoose");
const { Book, Page } = require("./src/models");

async function checkPages() {
  try {
    await mongoose.connect(process.env.MONGODB_URI || "mongodb://localhost:27017/text_information_retrieval");
    console.log("✅ Connected to MongoDB");

    const bookId = "699cde090b053d9c7b55e5ff";
    
    // Get book
    const book = await Book.findById(bookId);
    console.log("\n📚 Book:", {
      id: book._id,
      title: book.title,
      totalPages: book.totalPages,
      status: book.status
    });

    // Get pages
    const pages = await Page.find({ bookId: bookId });
    console.log(`\n📄 Pages found: ${pages.length}`);
    
    pages.forEach((page, i) => {
      console.log(`  Page ${page.pageNumber}: ${page.text ? page.text.substring(0, 100) : '(empty)'}...`);
    });

    // Check all pages (without filter)
    const allPages = await Page.find({});
    console.log(`\n📄 Total pages in database: ${allPages.length}`);

    await mongoose.disconnect();
    console.log("\n✅ Done");
  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
}

checkPages();
