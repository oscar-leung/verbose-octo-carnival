import { test, expect } from '../fixtures/auth.fixture.js';
import { PRODUCTS } from '../data/products.js';

test.describe('Checkout @regression', () => {
  test('completes a happy-path order @smoke', async ({
    authedInventoryPage,
    cartPage,
    checkoutPage,
    page,
  }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.openCart();
    await cartPage.checkout();

    await checkoutPage.fillInfo('Ada', 'Lovelace', '94107');
    await checkoutPage.submitInfo();

    const subtotal = await checkoutPage.subtotal();
    const tax = await checkoutPage.tax();
    const total = await checkoutPage.total();
    expect(subtotal).toBeGreaterThan(0);
    expect(total).toBeCloseTo(subtotal + tax, 2);

    await checkoutPage.finish();
    await expect(checkoutPage.successHeader).toHaveText(/thank you/i);
    await expect(page).toHaveURL(/checkout-complete\.html$/);
  });

  test('requires first name', async ({
    authedInventoryPage,
    cartPage,
    checkoutPage,
  }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.openCart();
    await cartPage.checkout();

    await checkoutPage.fillInfo('', 'Lovelace', '94107');
    await checkoutPage.submitInfo();
    await expect(checkoutPage.errorMessage).toContainText(/first name is required/i);
  });

  test('requires last name', async ({
    authedInventoryPage,
    cartPage,
    checkoutPage,
  }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.openCart();
    await cartPage.checkout();

    await checkoutPage.fillInfo('Ada', '', '94107');
    await checkoutPage.submitInfo();
    await expect(checkoutPage.errorMessage).toContainText(/last name is required/i);
  });

  test('requires postal code', async ({
    authedInventoryPage,
    cartPage,
    checkoutPage,
  }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.openCart();
    await cartPage.checkout();

    await checkoutPage.fillInfo('Ada', 'Lovelace', '');
    await checkoutPage.submitInfo();
    await expect(checkoutPage.errorMessage).toContainText(/postal code is required/i);
  });
});
