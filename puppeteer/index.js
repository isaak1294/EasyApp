import puppeteer from 'puppeteer-extra';
import fs from 'fs/promises';
import path from 'path';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

const cookiesFilePath = path.resolve('./', 'cookies.json');

async function saveCookies(page) {
  const cookies = await page.cookies();
  await fs.writeFile(cookiesFilePath, JSON.stringify(cookies, null, 2));
  console.log('Cookies saved to: ', cookiesFilePath);
}

async function loadCookies(page) {
  try {
    const cookiesString = await fs.readFile(cookiesFilePath, 'utf-8');
    const cookies = JSON.parse(cookiesString);
    await page.setCookie(...cookies);
    console.log('Cookies loaded from: ', cookiesFilePath);
  } catch (error) {
    console.error('Failed to load cookies:', error);
  }
}


(async () => {
  // Launch the browser and open a new blank page
  const browser = await puppeteer.launch({
    headless: false,
    userDataDir: './user_data'
  });
  const page = await browser.newPage();

  await loadCookies(page);

  // Navigate the page to a URL
  await page.goto('https://learninginmotion.uvic.ca/students/NetlinkID/student-login.htm');

  // Wait for the page to load
  
  await page.waitForSelector('input[name="username"]');
  await page.waitForSelector('input[name="password"]');

    // Type the username and password
    await page.type('input[name="username"]', '');
    await page.type('input[name="password"]', '');

    // Click the login button
    await page.waitForSelector('button[name="submitBtn"]');
    await page.click('button[name="submitBtn"]');
    await page.waitForNavigation();

    // Wait for the page to load
    try{
      if(await page.waitForSelector('button[id="trust-browser-button"]', {timeout: 10000})){
      await page.click('button[id="trust-browser-button"]');
      saveCookies(page);
      }
    }catch(e){
      console.log("No trust button");
    }

    
    // Wait for the page to load
    await page.goto('https://learninginmotion.uvic.ca/myAccount/co-op/postings.htm');
    await page.waitForSelector('a[onclick*="displayQuickSearch"]');
    // Click on the link with the specific text "- Summer -"
    await page.evaluate(() => {
      const links = document.querySelectorAll('a[onclick*="displayQuickSearch"]');
      for (let link of links) {
        if (link.textContent.includes('New postings')) {
          link.click();
          break;
        }
      }
    });
    await page.waitForSelector('table[id="postingsTable"]');

    // Scroll through the table to load all jobs
    let previousHeight;
    while (true) {
      const currentHeight = await page.evaluate('document.body.scrollHeight');
      if (previousHeight === currentHeight) {
        break;
      }
      previousHeight = currentHeight;
      await page.evaluate('window.scrollTo(0, document.body.scrollHeight)', {timeout: 1000}); // Wait for new content to load
    }

    // Extract job information from the table
    const jobs = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('table[id="postingsTable"] tr'));
      console.log(`Found ${rows.length} rows in the table`);
      return rows.slice(1).map(row => {
        const columns = row.querySelectorAll('td');
        return {
          appStatus: columns[1]?.innerText.trim() || '',
          id: columns[2]?.innerText.trim() || '',
          title: columns[3]?.innerText.trim() || '',
          employer: columns[4]?.innerText.trim() || '',
          division: columns[5]?.innerText.trim() || '',
          location: columns[7]?.innerText.trim() || ''
        };
      });
    });

    try {
      const jobsFilePath = path.resolve('./', 'jobs.json');
      await fs.writeFile(jobsFilePath, JSON.stringify(jobs, null, 2));
      console.log('Jobs saved to: ', jobsFilePath);
    } catch (error) {
      console.error('Error writing to jobs.json:', error);
    }

// Visit each job posting page
for (const job of jobs) {
  const jobFilePath = path.resolve('./jobs/', `job-${job.id}.json`);
  try{
    await access(jobFilePath);
    continue;
  }
  catch{
    const jobClass = `np-view-btn-${job.id}`;
    let retries = 3;
    while (retries > 0) {
      try {
        await page.waitForSelector(`a.${jobClass}`, { timeout: 5000 });
        console.log(`Found job link for: ${job.title}`);

        const [newPage] = await Promise.all([
          new Promise((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error('Timeout waiting for targetcreated')), 10000);
            browser.once('targetcreated', async target => {
              const page = await target.page();
              if (page) {
                clearTimeout(timeout);
                resolve(page);
              } else {
                clearTimeout(timeout);
                reject(new Error('Target created but no page found'));
              }
            });
          }),
          page.click(`a.${jobClass}`)
        ]);

        console.log(`Clicked on job posting: ${job.title}`);
        await newPage.waitForSelector('h1', { timeout: 10000 });
        console.log(`Visited job posting: ${job.title}`);

        // Perform any additional actions on the job posting page
        const jobDetails = await newPage.evaluate(() => {
          const title = document.querySelector('h1')?.innerText.trim() || '';
          
          // Assuming the correct table is the first table on the page
          const table = document.querySelectorAll('table')[3]; // Adjust the index as needed
          const rows = Array.from(table.querySelectorAll('tr'));
          console.log(`Found ${rows.length} rows in the table`);
        
          return {
            title,
            details: rows.slice(0).map(row => { // Extract rows 0-7
              const columns = row.querySelectorAll('td');
              return {
                key: columns[0]?.innerText.trim() || '',
                value: columns[1]?.innerText.trim() || ''
              };
            })
          };
        });

        await fs.writeFile(jobFilePath, JSON.stringify(jobDetails, null, 2));
        console.log(`Job details saved to: ${jobFilePath}`);


        // Close the new tab
        await newPage.close();
        await page.bringToFront();
        break; // Exit the retry loop if successful
      } catch (error) {
        console.error(`Error visiting job posting with ID ${job.id}:`, error);
        retries -= 1;
        if (retries > 0) {
          console.log(`Retrying... (${3 - retries} attempts left)`);
        } else {
          console.log(`Failed to visit job posting with ID ${job.id} after multiple attempts.`);
        }
      }
    }
  }
}

await browser.close();
})();