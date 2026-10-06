/**
 * fnt_session_extractor.js — Hermes Skill: fnt-session-fetch
 *
 * Automated Playwright script to fetch a fresh FNT Command session ID:
 * 1. Log into FNT Command at https://100.80.103.95/app/command
 * 2. Select Mandant
 * 3. Search Active Sessions at /html/administration/search/session
 * 4. Extract active session IDs & sessionid cookies
 * 5. Update .env files across the cable-scanner workspaces (source of truth + copies)
 */

let playwright;
try {
  playwright = require('playwright');
} catch (e1) {
  try {
    playwright = require('/home/ubuntu/.gemini/antigravity-cli/brain/e0d69319-7984-460d-9967-35fb67f3d12c/scratch/node_modules/playwright');
  } catch (e2) {
    console.error('❌ Playwright module not found. Please run: npm install playwright');
    process.exit(1);
  }
}

const { chromium } = playwright;
const fs = require('fs');
const path = require('path');

const FNT_URL = process.env.FNT_BASE_URL || 'https://100.80.103.95/app/command';
const FNT_USER = process.env.FNT_USERNAME || 'command';
const FNT_PASS = process.env.FNT_PASSWORD || 'command';

// Source of truth first, then other workspaces, then cwd fallback.
const ENV_PATHS = Array.from(
  new Set([
    '/home/ubuntu/cable-scanner-fnt/.env',
    path.join(process.cwd(), '.env'),
  ])
);

(async () => {
  console.log('--------------------------------------------------');
  console.log('🔌 FNT Command Session Extractor (fnt-session-fetch)');
  console.log('--------------------------------------------------');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1400, height: 900 }
  });

  const page = await context.newPage();

  try {
    // 1. Open FNT Command
    console.log(`\n[1/5] Navigating to ${FNT_URL} ...`);
    await page.goto(FNT_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // 2. Login
    console.log(`[2/5] Logging in as user '${FNT_USER}'...`);
    await page.fill('#userName', FNT_USER);
    await page.fill('#password', FNT_PASS);
    await Promise.all([
      page.click('button:has-text("OK")'),
      page.waitForTimeout(3000)
    ]);

    // 3. Mandant selection
    console.log('[3/5] Handling Mandant selection...');
    if (!page.url().includes('mandant')) {
      try {
        await page.goto(`${FNT_URL}/html/command/mandant`, { waitUntil: 'networkidle', timeout: 15000 });
        await page.waitForTimeout(2000);
      } catch (e) {}
    }

    const okButtons = await page.$$('button:has-text("OK")');
    if (okButtons.length > 0) {
      await okButtons[okButtons.length - 1].click();
      await page.waitForTimeout(3000);
    }

    // 4. Session Administration Search
    console.log('[4/5] Navigating to Session Search...');
    await page.goto(`${FNT_URL}/html/administration/search/session`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);

    const searchBtn = await page.$('button:has-text("Search")') ||
                      await page.$('button:has-text("Suchen")') ||
                      await page.$('button[type="submit"]') ||
                      await page.$('button');

    if (searchBtn) {
      console.log('   Clicking Search...');
      await searchBtn.click();
      await page.waitForTimeout(4000);
    }

    // 5. Extract Session Info
    console.log('\n[5/5] Extracting Session Tokens...');

    const cookies = await context.cookies();
    const sessionCookie = cookies.find(c => c.name.toLowerCase() === 'sessionid')?.value;

    const fullText = await page.evaluate(() => document.body.innerText);
    const sessionMatches = fullText.match(/[a-zA-Z0-9_-]{20,}/g) || [];
    const activeSessionId = sessionCookie || sessionMatches[0] || 'Unknown';

    console.log('\n==================================================');
    console.log('🔑 Active FNT Session ID:', activeSessionId);
    console.log('==================================================');

    if (activeSessionId === 'Unknown' || activeSessionId.length < 20) {
      console.error('❌ Session extraction FAILED — no valid token found.');
      process.exit(2);
    }

    // 6. Update .env files across workspaces
    let envContent = `FNT_BASE_URL=${FNT_URL}\nFNT_USERNAME=${FNT_USER}\nFNT_PASSWORD=${FNT_PASS}\nFNT_SESSION_ID=${activeSessionId}\n`;
    for (const targetPath of ENV_PATHS) {
      try {
        fs.writeFileSync(targetPath, envContent);
        console.log(`✅ Saved updated session ID to: ${targetPath}`);
      } catch (e) {}
    }

  } catch (err) {
    console.error('\n❌ Extraction error:', err.message);
    process.exit(2);
  } finally {
    await browser.close();
    console.log('\nDone.');
  }
})();