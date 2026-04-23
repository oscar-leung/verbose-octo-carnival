import { test, expect } from '../fixtures/auth.fixture.js';
import { USERS } from '../data/users.js';

test.describe('Authentication @regression', () => {
  test('standard user can log in @smoke', async ({ loginPage, inventoryPage }) => {
    await loginPage.goto();
    await loginPage.login(USERS.standard.username, USERS.standard.password);
    await expect(inventoryPage.container).toBeVisible();
    expect(loginPage.url).toContain('/inventory.html');
  });

  test('locked-out user sees error message', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login(USERS.locked.username, USERS.locked.password);
    const error = await loginPage.expectError();
    expect(error).toMatch(/locked out/i);
  });

  test('empty credentials are rejected', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('', '');
    expect(await loginPage.expectError()).toMatch(/username is required/i);
  });

  test('missing password is rejected', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login(USERS.standard.username, '');
    expect(await loginPage.expectError()).toMatch(/password is required/i);
  });

  test('invalid credentials are rejected', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('not_a_user', 'bad_password');
    expect(await loginPage.expectError()).toMatch(/do not match|username and password/i);
  });

  test('user can log out', async ({ authedInventoryPage, page }) => {
    await authedInventoryPage.logout();
    await expect(page).toHaveURL(/\/$|\/index\.html/);
  });
});
