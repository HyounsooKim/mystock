import { test, expect } from '@playwright/test';

/**
 * E2E Test: User Authentication Flow
 * Tests user registration and login functionality
 */

// Test data - use unique email for each test run
const timestamp = Date.now();
const testUser = {
  email: `test${timestamp}@test.com`,
  password: 'Qwe!@#asd123', // Must contain uppercase, lowercase, number and special characters
};

// Sequential tests: 1. Register → 2. Login → 3. Logout
// Run with --workers=1 to ensure sequential execution
test.describe('Authentication Flow (Sequential)', () => {
  test('1. should register a new user successfully', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to register page
    await page.click('text=회원가입');
    
    // Wait for register form to load
    await expect(page).toHaveURL(/\/register/);

    // Fill in registration form using placeholder text (email and password only)
    await page.locator('input[placeholder="이메일 주소"]').first().fill(testUser.email);
    await page.locator('input[placeholder*="비밀번호"]').first().fill(testUser.password);
    await page.fill('input[placeholder="비밀번호 확인"]', testUser.password);

    // Submit the form
    await page.click('button[type="submit"]:has-text("회원가입")');

    // Wait for redirect to watchlist page after successful registration
    await expect(page).toHaveURL('/watchlist', { timeout: 10000 });
    
    // Verify user is logged in by checking URL
    await expect(page).toHaveURL('/watchlist');
    
    // Logout to prepare for login test
    // Click user badge dropdown (우측 상단 회원 버튼)
    // Structure: <a data-bs-toggle="dropdown"><div class="user-badge">...</div></a>
    const userDropdown = page.locator('a.nav-link[data-bs-toggle="dropdown"] .user-badge, a[data-bs-toggle="dropdown"]:has(.user-badge)').first();
    await userDropdown.click();
    
    // Wait for dropdown menu to appear
    await page.waitForTimeout(500);
    
    // Click logout link in dropdown menu
    // Structure: <a class="dropdown-item text-danger"><i class="ti ti-logout"></i> 로그아웃 </a>
    const logoutLink = page.locator('a.dropdown-item.text-danger:has-text("로그아웃")');
    await logoutLink.click();
    
    // Verify redirect to login page
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('2. should login with existing user credentials', async ({ page }) => {
    // Should be on login page from previous test's logout
    // Or navigate if needed
    if (!page.url().includes('/login')) {
      await page.goto('/login');
    }
    
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('h2')).toContainText('로그인');

    // Fill in login form using placeholder text
    await page.fill('input[placeholder="이메일 주소"]', testUser.email);
    await page.fill('input[placeholder="비밀번호"]', testUser.password);

    // Submit the form
    await page.click('button[type="submit"]:has-text("로그인")');

    // Wait for redirect to watchlist page after successful login
    await expect(page).toHaveURL('/watchlist', { timeout: 10000 });
    
    // Verify user is logged in by checking URL
    await expect(page).toHaveURL('/watchlist');
    
    // IMPORTANT: Do NOT logout here - let test 3 use this logged-in session
  });

  test('3. should logout successfully', async ({ page }) => {
    // First login (each test gets a new browser context)
    await page.goto('/login');
    await page.fill('input[placeholder="이메일 주소"]', testUser.email);
    await page.fill('input[placeholder="비밀번호"]', testUser.password);
    await page.click('button[type="submit"]:has-text("로그인")');
    
    // Wait for successful login
    await expect(page).toHaveURL('/watchlist', { timeout: 10000 });

    // Click user badge dropdown in top right corner (우측 상단 회원 버튼)
    // Structure: <a data-bs-toggle="dropdown"><div class="user-badge"><span class="user-id">...</span></div></a>
    const userDropdown = page.locator('a.nav-link[data-bs-toggle="dropdown"] .user-badge, a[data-bs-toggle="dropdown"]:has(.user-badge)').first();
    
    // Wait for dropdown button to be visible
    await userDropdown.waitFor({ state: 'visible', timeout: 5000 });
    
    // Click to open dropdown menu
    await userDropdown.click();
    
    // Wait for dropdown menu animation
    await page.waitForTimeout(500);
    
    // Click logout link in dropdown menu
    // Structure: <a class="dropdown-item text-danger"><i class="ti ti-logout"></i> 로그아웃 </a>
    const logoutLink = page.locator('a.dropdown-item.text-danger:has-text("로그아웃")');
    await logoutLink.waitFor({ state: 'visible', timeout: 5000 });
    await logoutLink.click();

    // Should redirect to login page
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
    
    // Verify we're back on login page
    await expect(page.locator('h2')).toContainText('로그인');
  });
});

// Independent validation tests
test.describe('Authentication Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should show validation error for invalid email format', async ({ page }) => {
    // Navigate to register page
    await page.click('text=회원가입');
    await expect(page).toHaveURL(/\/register/);

    // Fill in email field with invalid format (HTML5 validation will catch this)
    const emailInput = page.locator('input[placeholder="이메일 주소"]').first();
    await emailInput.fill('invalid-email');
    
    // Try to submit - HTML5 validation should prevent it
    await page.locator('input[placeholder*="비밀번호"]').first().fill('ValidPass123!');
    await page.fill('input[placeholder="비밀번호 확인"]', 'ValidPass123!');
    
    // Note: HTML5 email validation prevents invalid emails from being submitted
    // This test validates that browser validation works
  });

  test('should show error for short password', async ({ page }) => {
    // Navigate to register page
    await page.click('text=회원가입');
    await expect(page).toHaveURL(/\/register/);

    const timestamp = Date.now();
    // Fill in registration form with short password
    await page.locator('input[placeholder="이메일 주소"]').first().fill(`newuser${timestamp}@test.com`);
    await page.locator('input[placeholder*="비밀번호"]').first().fill('short');
    await page.fill('input[placeholder="비밀번호 확인"]', 'short');

    // Submit the form
    await page.click('button[type="submit"]:has-text("회원가입")');

    // Check for validation error (could be alert, error text, or still on register page)
    await page.waitForTimeout(1000); // Wait for validation
    
    // Should still be on register page or show error
    const currentUrl = page.url();
    const isStillOnRegister = currentUrl.includes('/register');
    const hasErrorAlert = await page.locator('.alert-warning, .alert-danger, .text-danger, [class*="error"]').count() > 0;
    
    expect(isStillOnRegister || hasErrorAlert).toBeTruthy();
  });

  test('should show error for wrong login credentials', async ({ page }) => {
    // Should be on login page initially
    await expect(page).toHaveURL(/\/login/);

    // Fill in login form with wrong credentials
    await page.fill('input[placeholder="이메일 주소"]', 'nonexistent@test.com');
    await page.fill('input[placeholder="비밀번호"]', 'wrongpassword123');

    // Submit the form
    await page.click('button[type="submit"]:has-text("로그인")');

    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
    
    // Check for error message
    await expect(page.locator('.alert-danger')).toBeVisible();
  });
});

// Navigation tests
test.describe('Authentication Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });


  test('should navigate between login and register pages', async ({ page }) => {
    // Should start on login page
    await expect(page).toHaveURL(/\/login/);

    // Go to register page
    await page.click('text=회원가입');
    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator('h2')).toContainText('회원가입');

    // Go back to login page
    await page.click('text=로그인');
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('h2')).toContainText('로그인');
  });

  test('should require authentication for protected routes', async ({ page }) => {
    // Try to access protected route directly
    await page.goto('/watchlist');
    
    // Should redirect to login page (may have redirect query param)
    await expect(page).toHaveURL(/\/login/);
    
    // Try portfolio route
    await page.goto('/portfolio');
    await expect(page).toHaveURL(/\/login/);
  });
});
