require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { analyzeWithGemini } = require('./geminiClient');

const app = express();
const port = process.env.PORT || 5174;

app.use(cors());
app.use(express.json({ limit: '1mb' }));

app.post('/api/analyze', async (req, res) => {
  try {
    const { code, language, model } = req.body || {};
    if (!code || !code.trim()) {
      return res.status(400).json({ error: 'No code provided' });
    }

    const result = await analyzeWithGemini({ code, language, model });

    return res.json({ result });
  } catch (err) {
    console.error('Analyze error', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.listen(port, () => {
  console.log(`Lets-Run backend listening on http://localhost:${port}`);
});
