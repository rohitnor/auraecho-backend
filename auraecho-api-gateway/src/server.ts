import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { Pool } from 'pg';
import axios from 'axios';
import rateLimit from 'express-rate-limit'; // 1. Add this import

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// 2. Create the Rate Limiter rule
const apiLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute memory window
  max: 3, // Limit each IP to exactly 3 requests per minute
  message: { error: 'Traffic limit exceeded. Please wait 60 seconds.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// 3. Apply the rule ONLY to your API endpoints
app.use('/api/', apiLimiter);

// Initialize PostgreSQL connection pool using Neon connection string
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const FASTAPI_URL = 'http://127.0.0.1:8000';

// API orchestrator route
app.post('/api/analyze', async (req, res) => {
  const { raw_text } = req.body;

  if (!raw_text) {
    return res.status(400).json({ error: 'Text content is required' });
  }

  try {
    // 1. Hand off heavy math/AI text analysis to FastAPI
    const aiResponse = await axios.post(`${FASTAPI_URL}/analyze`, { raw_text });
    const { summary, key_themes } = aiResponse.data;

    // 2. Persist metadata logs to PostgreSQL inside Node.js layer
    const dbResult = await pool.query(
      'INSERT INTO notes (raw_text, summary, key_themes) VALUES ($1, $2, $3) RETURNING id;',
      [raw_text, summary, key_themes]
    );

    // 3. Respond back to Next.js client
    return res.status(200).json({
      id: dbResult.rows[0].id,
      summary,
      key_themes,
    });
  } catch (error: any) {
    console.error('Error in orchestrator layer:', error.message);
    return res.status(500).json({ error: 'Internal server orchestration failure' });
  }
});

// API search route
app.post('/api/search', async (req, res) => {
  const { query } = req.body;

  if (!query) {
    return res.status(400).json({ error: 'Search query is required' });
  }

  try {
    // Forward the search request to the Python AI engine
    const searchResponse = await axios.post(`${FASTAPI_URL}/search`, { query });
    
    // Return the semantic matches back to Next.js
    return res.status(200).json(searchResponse.data);
  } catch (error: any) {
    console.error('Error in search routing layer:', error.message);
    return res.status(500).json({ error: 'Internal server search failure' });
  }
});

const PORT = parseInt(process.env.PORT || '5000', 10);

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
});