const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const b = await chromium.launch();
  const pg = await b.newPage();
  for (const j of jobs) {
    await pg.goto('file://' + j.html, { waitUntil: 'load' });
    await pg.evaluate(() => document.fonts.ready);
    await pg.pdf({ path: j.out, format: 'A4', printBackground: true, displayHeaderFooter: true,
      headerTemplate: '<span></span>', footerTemplate: j.foot,
      margin: { top: '14mm', bottom: '16mm', left: '15mm', right: '15mm' } });
    console.log(fs.statSync(j.out).size, j.out.split('/pdf2/')[1]);
  }
  await b.close();
})();
