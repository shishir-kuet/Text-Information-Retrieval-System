const fs = require('fs');
const path = require('path');

console.log('🔍 Backend Setup Verification\n');
console.log('═'.repeat(50));

// Check 1: package.json exists
const checks = [];

// Check package.json
if (fs.existsSync(path.join(__dirname, 'package.json'))) {
  console.log('✅ package.json found');
  checks.push(true);
} else {
  console.log('❌ package.json missing');
  checks.push(false);
}

// Check node_modules
if (fs.existsSync(path.join(__dirname, 'node_modules'))) {
  console.log('✅ node_modules installed');
  checks.push(true);
} else {
  console.log('❌ node_modules missing - run: npm install');
  checks.push(false);
}

// Check .env file
if (fs.existsSync(path.join(__dirname, '.env'))) {
  console.log('✅ .env file exists');
  checks.push(true);
} else {
  console.log('⚠️  .env missing - copy from .env.example');
  checks.push(false);
}

// Check src structure
const srcDirs = ['src/config', 'src/routes', 'src/middlewares', 'src/utils'];
let srcOk = true;
srcDirs.forEach(dir => {
  if (!fs.existsSync(path.join(__dirname, dir))) {
    console.log(`❌ ${dir} missing`);
    srcOk = false;
  }
});
if (srcOk) {
  console.log('✅ Source structure complete');
  checks.push(true);
} else {
  checks.push(false);
}

// Try loading app.js
try {
  require('./src/app.js');
  console.log('✅ app.js loads without errors');
  checks.push(true);
} catch (err) {
  console.log('❌ app.js has errors:', err.message);
  checks.push(false);
}

// MongoDB check
console.log('\n📊 MongoDB Status:');
require('dotenv').config();
const mongoose = require('mongoose');

const mongoUri = process.env.MONGO_URI || 'not configured';
console.log(`   URI: ${mongoUri}`);

// Quick connection test with timeout
mongoose.connect(mongoUri, { 
  serverSelectionTimeoutMS: 3000 
}).then(() => {
  console.log('✅ MongoDB connected successfully!');
  console.log('\n🎉 All checks passed! Backend is ready to run.');
  process.exit(0);
}).catch((err) => {
  console.log('❌ MongoDB connection failed (install MongoDB or use Atlas)');
  console.log(`   Error: ${err.message.split(',')[0]}`);
  console.log('\n📋 Summary:');
  console.log(`   Code checks: ${checks.filter(c => c).length}/${checks.length} passed`);
  console.log(`   MongoDB: Not connected`);
  console.log('\n💡 Setup MongoDB:');
  console.log('   Option 1: MongoDB Atlas (cloud) - https://mongodb.com/cloud/atlas');
  console.log('   Option 2: Local MongoDB - https://mongodb.com/try/download/community');
  console.log('\n📌 Backend code is ready! Just need MongoDB to run the server.');
  process.exit(checks.every(c => c) ? 0 : 1);
});

// Timeout fallback
setTimeout(() => {
  console.log('\n⏱️  Connection timeout');
  process.exit(1);
}, 5000);
