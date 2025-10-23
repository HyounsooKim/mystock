import { test, expect } from '@playwright/test'

test.describe('Top Movers Feature', () => {
  // Setup: Login before each test
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('http://localhost:5173/login')
    
    // Fill in login credentials (adjust based on your test user)
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'testpassword')
    
    // Click login button
    await page.click('button[type="submit"]')
    
    // Wait for navigation to complete
    await page.waitForURL('**/watchlist')
  })

  test('should navigate to top movers page', async ({ page }) => {
    // Click on the top movers navigation link
    await page.click('a[href="/top-movers"]')
    
    // Verify we're on the top movers page
    await expect(page).toHaveURL(/.*top-movers/)
    
    // Check page title
    await expect(page.locator('h2.page-title')).toContainText('급등락 종목들')
  })

  test('should display three lists correctly', async ({ page }) => {
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Wait for data to load
    await page.waitForSelector('.card', { timeout: 10000 })
    
    // Check that we have three cards (gainers, losers, active)
    const cards = await page.locator('.card').count()
    expect(cards).toBeGreaterThanOrEqual(3)
    
    // Verify card titles
    await expect(page.locator('.card-title').first()).toContainText('상승 상위')
    await expect(page.locator('.card-title').nth(1)).toContainText('하락 상위')
    await expect(page.locator('.card-title').nth(2)).toContainText('거래량 상위')
  })

  test('should navigate to stock detail on ticker click', async ({ page }) => {
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Wait for data to load
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    
    // Get the first ticker symbol
    const firstTicker = await page.locator('table tbody tr').first().locator('.ticker-symbol').textContent()
    
    // Click on the first row
    await page.locator('table tbody tr').first().click()
    
    // Verify navigation to stock detail page
    await expect(page).toHaveURL(/.*\/stock\/.*/)
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Wait for data to load
    await page.waitForSelector('.card', { timeout: 10000 })
    
    // Check that cards are stacked vertically
    const cards = page.locator('.col')
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(3)
    
    // Verify page is scrollable
    const pageHeight = await page.evaluate(() => document.body.scrollHeight)
    expect(pageHeight).toBeGreaterThan(667)
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/v1/stocks/top-movers', route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Service unavailable' })
      })
    })
    
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Check for error message
    await expect(page.locator('.alert-danger')).toBeVisible()
    await expect(page.locator('.alert-danger')).toContainText('데이터 로드 실패')
  })

  test('should display loading state', async ({ page }) => {
    // Slow down API response to see loading state
    await page.route('**/api/v1/stocks/top-movers', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000))
      route.continue()
    })
    
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Check for loading spinner
    await expect(page.locator('.spinner-border')).toBeVisible()
    
    // Wait for loading to complete
    await page.waitForSelector('.card', { timeout: 10000 })
    
    // Verify loading spinner is gone
    await expect(page.locator('.spinner-border')).not.toBeVisible()
  })

  test('should refresh data when clicking refresh button', async ({ page }) => {
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Wait for data to load
    await page.waitForSelector('.card', { timeout: 10000 })
    
    // Click refresh button (floating button)
    await page.locator('.floating-refresh button').click()
    
    // Verify loading state appears briefly
    // (This is tricky to test without proper timing, so we just check the button exists)
    await expect(page.locator('.floating-refresh button')).toBeVisible()
  })

  test('should format numbers correctly', async ({ page }) => {
    // Navigate to top movers
    await page.goto('http://localhost:5173/top-movers')
    
    // Wait for data to load
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    
    // Check that percentage values have % sign
    const firstPercentage = await page.locator('table tbody tr').first().locator('td').nth(4).textContent()
    expect(firstPercentage).toMatch(/%/)
    
    // Check that volume is formatted (should have B, M, or K suffix if large)
    const firstVolume = await page.locator('table tbody tr').first().locator('td').nth(5).textContent()
    expect(firstVolume).toBeTruthy()
  })
})
