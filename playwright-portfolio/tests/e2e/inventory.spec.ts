import { test, expect } from '../fixtures/auth.fixture.js';
import { EXPECTED_INVENTORY_COUNT, PRODUCTS } from '../data/products.js';

test.describe('Inventory @regression', () => {
  test('displays the expected number of products @smoke', async ({ authedInventoryPage }) => {
    await expect(authedInventoryPage.items).toHaveCount(EXPECTED_INVENTORY_COUNT);
  });

  test('sorts products by name A→Z', async ({ authedInventoryPage }) => {
    await authedInventoryPage.sortBy('az');
    const names = await authedInventoryPage.itemNameList();
    const sorted = [...names].sort((a, b) => a.localeCompare(b));
    expect(names).toEqual(sorted);
  });

  test('sorts products by name Z→A', async ({ authedInventoryPage }) => {
    await authedInventoryPage.sortBy('za');
    const names = await authedInventoryPage.itemNameList();
    const sorted = [...names].sort((a, b) => b.localeCompare(a));
    expect(names).toEqual(sorted);
  });

  test('sorts products by price low→high', async ({ authedInventoryPage }) => {
    await authedInventoryPage.sortBy('lohi');
    const prices = await authedInventoryPage.itemPriceList();
    const sorted = [...prices].sort((a, b) => a - b);
    expect(prices).toEqual(sorted);
  });

  test('sorts products by price high→low', async ({ authedInventoryPage }) => {
    await authedInventoryPage.sortBy('hilo');
    const prices = await authedInventoryPage.itemPriceList();
    const sorted = [...prices].sort((a, b) => b - a);
    expect(prices).toEqual(sorted);
  });

  test('adding an item increments the cart badge', async ({ authedInventoryPage }) => {
    expect(await authedInventoryPage.cartCount()).toBe(0);
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    expect(await authedInventoryPage.cartCount()).toBe(1);
  });

  test('removing an item decrements the cart badge', async ({ authedInventoryPage }) => {
    await authedInventoryPage.addToCart(PRODUCTS.backpack);
    await authedInventoryPage.addToCart(PRODUCTS.bikeLight);
    expect(await authedInventoryPage.cartCount()).toBe(2);
    await authedInventoryPage.removeFromCart(PRODUCTS.backpack);
    expect(await authedInventoryPage.cartCount()).toBe(1);
  });
});
