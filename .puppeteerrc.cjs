const {join} = require('path');
module.exports = {
  executablePath: '/usr/bin/google-chrome-stable',
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
  headless: true,
};
