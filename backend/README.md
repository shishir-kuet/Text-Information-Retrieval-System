# Backend - Text Information Retrieval System

Express.js backend with MongoDB for the book search system.

## Quick Start

\`\`\`bash

# Install dependencies

npm install

# Copy environment file

cp .env.example .env

# Edit .env and add your MongoDB URI

# Start development server

npm run dev
\`\`\`

## Environment Variables

Create `.env` file (see `.env.example`):

- `PORT` - Server port (default: 5000)
- `MONGO_URI` - MongoDB connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `NODE_ENV` - Environment (development/production)

## Scripts

- `npm run dev` - Start with nodemon (hot reload)
- `npm start` - Start production server

## Project Structure

\`\`\`
src/
├── app.js # Express app configuration
├── server.js # Server entry point
├── config/
│ └── db.js # MongoDB connection
├── routes/ # API routes
├── controllers/ # Route handlers
├── models/ # Mongoose schemas
├── services/ # Business logic
├── middlewares/ # Custom middleware
└── utils/ # Helper functions
\`\`\`

## API Endpoints

### Current

- `GET /api/health` - Health check

### Coming Soon

- Authentication routes
- Book management routes
- Search endpoint
- Admin routes

## Dependencies

- express - Web framework
- mongoose - MongoDB ODM
- cors - CORS middleware
- helmet - Security headers
- dotenv - Environment config
- morgan - Request logging
- express-rate-limit - Rate limiting
