import type { Locator, Page } from '@playwright/test';
import { BasePage } from './base.page.js';

export type SortOption = 'az' | 'za' | 'lohi' | 'hilo';

export class InventoryPage extends BasePage {
  readonly path = '/inventory.html';

  readonly container: Locator;
  readonly items: Locator;
  readonly itemNames: Locator;
  readonly itemPrices: Locator;
  readonly sortDropdown: Locator;
  readonly cartBadge: Locator;
  readonly cartLink: Locator;
  readonly burgerMenu: Locator;
  readonly logoutLink: Locator;

  constructor(page: Page) {
    super(page);
    this.container = page.locator('#inventory_container');
    this.items = page.locator('.inventory_item');
    this.itemNames = page.locator('.inventory_item_name');
    this.itemPrices = page.locator('.inventory_item_price');
    this.sortDropdown = page.locator('[data-test="product-sort-container"]');
    this.cartBadge = page.locator('.shopping_cart_badge');
    this.cartLink = page.locator('.shopping_cart_link');
    this.burgerMenu = page.locator('#react-burger-menu-btn');
    this.logoutLink = page.locator('#logout_sidebar_link');
  }

  async addToCart(itemName: string): Promise<void> {
    const item = this.items.filter({ hasText: itemName });
    await item.getByRole('button', { name: /add to cart/i }).click();
  }

  async removeFromCart(itemName: string): Promise<void> {
    const item = this.items.filter({ hasText: itemName });
    await item.getByRole('button', { name: /remove/i }).click();
  }

  async cartCount(): Promise<number> {
    if ((await this.cartBadge.count()) === 0) return 0;
    const text = (await this.cartBadge.textContent()) ?? '0';
    return parseInt(text.trim(), 10);
  }

  async sortBy(option: SortOption): Promise<void> {
    await this.sortDropdown.selectOption(option);
  }

  async itemNameList(): Promise<string[]> {
    return (await this.itemNames.allTextContents()).map((s) => s.trim());
  }

  async itemPriceList(): Promise<number[]> {
    const raw = await this.itemPrices.allTextContents();
    return raw.map((s) => parseFloat(s.replace('$', '').trim()));
  }

  async openCart(): Promise<void> {
    await this.cartLink.click();
  }

  async logout(): Promise<void> {
    await this.burgerMenu.click();
    await this.logoutLink.click();
  }
}
