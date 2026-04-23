import { test, expect } from '../fixtures/auth.fixture.js';
import { PRODUCTS } from '../data/products.js';

test.describe('Shopping cart @regression', () => {
  test('items added on inventory page appear in cart', async ({
    authedInventoryPage,
    cartPage,
  }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.addToCart(PRODUCTS.bikeLight);
    await authedInventoryPage.openCart();

    expect(await cartPage.itemCount()).toBe(2);
    const names = await cartPage.itemNameList();
    expect(names).toEqual(expect.arrayContaining([PRODUCTS.backpack, PRODUCTS.bikeLight]));
  });

  test('removing an item in the cart updates the badge @smoke', async ({
    authedInventoryPage,
    cartPage,
  }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.addToCart(PRODUCTS.bikeLight);
    await authedInventoryPage.openCart();

    await cartPage.removeItem(PRODUCTS.backpack);
    expect(await cartPage.itemCount()).toBe(1);
  });

  test('continue-shopping returns to inventory', async ({
    authedInventoryPage,
    cartPage,
    page,
  }) => {
    await authedInventoryPage.openCart();
    await cartPage.continueShopping();
    await expect(page).toHaveURL(/\/inventory\.html$/);
  });

  test('empty cart shows no items', async ({ authedInventoryPage, cartPage }) => {
    await authedInventoryPage.openCart();
    expect(await cartPage.itemCount()).toBe(0);
  });
});
