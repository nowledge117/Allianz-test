const express = require('express');
const app = express();
const port = 8080;

const color = process.env.APP_COLOR || 'black';
const version = process.env.npm_package_version || '1.0';

app.get('/', (req, res) => {
  res.send(`
    <body style="background-color:${color}; color:white; font-family:sans-serif; text-align:center;">
      <h1>Hello from the ${color.toUpperCase()} deployment!</h1>
      <h2>Version: ${version}</h2>
      <h3>Hostname: ${req.hostname}</h3>
    </body>
  `);
});

app.listen(port, () => {
  console.log(`App listening at http://localhost:${port}`);
});