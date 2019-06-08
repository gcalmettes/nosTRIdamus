const puppeteer = require('puppeteer');
const fs = require('fs')

const outputFileName = 'ironMan-active-races.json'
const filterWords = ['IRONMAN 70.3', 'IRONMAN']

const escapeXpathString = str => {
  const splitedQuotes = str.replace(/'/g, `', "'", '`);
  return `concat('${splitedQuotes}', '')`;
};

const clickByText = async (page, text) => {
  const escapedText = escapeXpathString(text);
  const linkHandlers = await page.$x(`//a/span[contains(text(), ${escapedText})]`);
  
  if (linkHandlers.length > 0) {
    await linkHandlers[0].click();
  } else {
    throw new Error(`Link not found: ${text}`);
  }
};


(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // go to races page
  await page.goto('http://www.ironman.com/events/triathlon-races.aspx');

  // click on filter to keep only filtered races
  for (const word of filterWords) {
    await clickByText(page, word);
    await page.waitFor(2000);
  }


  // scrape all IronKids races
  const allRaces = await page.evaluate(
    () => Array.from(document.querySelectorAll('article'))
      .map(article => {
        const name = article.querySelector("header>a>h2").textContent
        const url = article.querySelector("header>a").getAttribute("href")
        const location = article.querySelector("header>span").textContent
        return { name, url, location }
      })
  )


  // fs.writeFileSync('ironKids-races.json', JSON.stringify(allIronKidsRaces))
  const fileLogger = fs.createWriteStream(`./../data/races/${outputFileName}.json`, {
    flags: 'a' // 'a' means appending (old data will be preserved)
  })
  for (const race of allRaces) {
    fileLogger.write(`${JSON.stringify(race)}\n`)
  }

  console.log(allRaces)
  console.log(allRaces.length)
  // await page.screenshot({path: 'iron.png'});

  await browser.close();
})();