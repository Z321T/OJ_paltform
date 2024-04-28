const express = require('express');
const app = express();
const port = 3000;

app.get('/api', (req, res) => {
  res.json({ message: 'Hello from Node.js!' });
});

app.listen(port, () => {
  console.log(`Node.js server listening at http://localhost:${port}`);
});
