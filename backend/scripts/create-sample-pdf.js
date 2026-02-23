const PDFDocument = require("pdf-lib").PDFDocument;
const fs = require("fs").promises;
const path = require("path");

/**
 * Create a sample PDF for testing
 * This creates a simple text-based PDF that can be used to test the system
 */
async function createSamplePDF() {
  try {
    console.log("Creating sample PDF for testing...\n");

    // Create a new PDF document
    const pdfDoc = await PDFDocument.create();

    // Add pages with sample content
    const pages = [
      {
        title: "Page 1: Introduction to Information Retrieval",
        content: `Information Retrieval (IR) is the science of searching for information in documents, 
searching for documents themselves, and also searching for metadata that describe data, 
and for databases of texts, images or sounds. Information retrieval systems help users 
find information that matches their information needs.

The main components of an information retrieval system include:
- Document collection and indexing
- Query processing and analysis
- Ranking and retrieval algorithms
- User interface for interaction

Modern search engines like Google and Bing use sophisticated information retrieval 
techniques to provide relevant results to billions of users worldwide.`
      },
      {
        title: "Page 2: Inverted Index",
        content: `An inverted index is a data structure used to facilitate fast full-text searches. 
In an inverted index, each unique term in the corpus is mapped to a list of documents 
(or pages) where it appears.

The structure consists of:
- Term dictionary: stores unique terms
- Posting lists: for each term, stores document IDs and positions
- Document frequency: number of documents containing the term
- Term frequency: how often a term appears in each document

Inverted indexes are fundamental to search engines and enable efficient keyword searches 
across large document collections.`
      },
      {
        title: "Page 3: TF-IDF Algorithm",
        content: `TF-IDF stands for Term Frequency-Inverse Document Frequency. It is a numerical 
statistic that reflects how important a word is to a document in a collection.

Term Frequency (TF): measures how frequently a term occurs in a document. Since every 
document is different in length, it is often normalized.

Inverse Document Frequency (IDF): measures how important a term is. While computing TF, 
all terms are considered equally important. However, certain terms may appear very often 
but have little importance (like "the", "is", "of").

The TF-IDF score is calculated as: TF-IDF = TF × IDF

This scoring method helps in ranking documents by relevance to search queries.`
      },
      {
        title: "Page 4: Text Processing",
        content: `Text processing is a crucial step in building an information retrieval system. 
The main steps include:

1. Tokenization: breaking text into individual words or tokens
2. Normalization: converting text to lowercase
3. Stop word removal: filtering out common words
4. Stemming: reducing words to their root form
5. Lemmatization: similar to stemming but linguistically correct

These preprocessing steps help reduce the vocabulary size and improve search accuracy 
by treating related terms as equivalent.`
      },
      {
        title: "Page 5: Search and Ranking",
        content: `Search engines use various ranking algorithms to present the most relevant 
results to users. The ranking process involves:

- Query analysis and understanding user intent
- Document retrieval using inverted index
- Relevance scoring using algorithms like TF-IDF or BM25
- Result ranking based on computed scores
- Presenting top-k results to the user

Additional factors may include:
- Document authority and popularity
- Freshness of content
- User personalization
- Click-through rates

Modern search systems continue to evolve with machine learning and natural language 
processing techniques to better understand queries and documents.`
      }
    ];

    for (const pageData of pages) {
      const page = pdfDoc.addPage([600, 800]);
      const { height } = page.getSize();
      const fontSize = 12;
      const titleFontSize = 18;

      // Draw title
      page.drawText(pageData.title, {
        x: 50,
        y: height - 50,
        size: titleFontSize
      });

      // Draw content (simple wrapping)
      const words = pageData.content.split(" ");
      let line = "";
      let y = height - 100;
      const maxWidth = 500;

      for (const word of words) {
        const testLine = line + word + " ";
        
        // Simple width estimation (not perfect but works for testing)
        if (testLine.length * (fontSize * 0.5) > maxWidth) {
          page.drawText(line, { x: 50, y, size: fontSize });
          line = word + " ";
          y -= fontSize + 5;
        } else {
          line = testLine;
        }
      }
      
      // Draw remaining text
      if (line.length > 0) {
        page.drawText(line, { x: 50, y, size: fontSize });
      }
    }

    // Save the PDF
    const pdfBytes = await pdfDoc.save();
    const outputPath = path.join(__dirname, "../uploads", "sample-test-book.pdf");

    // Ensure uploads directory exists
    const uploadsDir = path.join(__dirname, "../uploads");
    try {
      await fs.mkdir(uploadsDir, { recursive: true });
    } catch (err) {
      // Directory already exists
    }

    await fs.writeFile(outputPath, pdfBytes);

    console.log("✅ Sample PDF created successfully!");
    console.log(`📄 File location: ${outputPath}`);
    console.log(`📊 Pages: ${pages.length}`);
    console.log(`💾 File size: ${(pdfBytes.length / 1024).toFixed(2)} KB\n`);

    console.log("📋 Content summary:");
    pages.forEach((p, i) => {
      console.log(`   Page ${i + 1}: ${p.title}`);
    });

    console.log("\n🧪 Testing keywords:");
    console.log("   - information, retrieval, system");
    console.log("   - inverted, index, search");
    console.log("   - tf-idf, algorithm, ranking");
    console.log("   - tokenization, stemming, processing");

    console.log("\n📝 Next steps:");
    console.log("   1. Start MongoDB: mongod");
    console.log("   2. Start backend: npm run dev");
    console.log("   3. Upload this PDF using Postman or cURL:");
    console.log(`      POST http://localhost:5000/api/books/upload`);
    console.log(`      Form data: pdf=@"${outputPath}", title="Sample Book", author="Test"`);
    console.log("   4. Build index: POST http://localhost:5000/api/index/build-all");
    console.log("   5. Check stats: GET http://localhost:5000/api/index/stats");

    return outputPath;
  } catch (error) {
    console.error("❌ Error creating sample PDF:", error.message);
    throw error;
  }
}

// Run if called directly
if (require.main === module) {
  createSamplePDF()
    .then(() => {
      console.log("\n✅ Sample PDF generation complete!");
      process.exit(0);
    })
    .catch((error) => {
      console.error("\n❌ Failed to create sample PDF:", error);
      process.exit(1);
    });
}

module.exports = createSamplePDF;
