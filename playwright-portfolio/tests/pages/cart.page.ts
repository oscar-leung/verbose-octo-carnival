import type { Locator, Page } from '@playwright/test';
import { BasePage } from './base.page.js';

export class CartPage extends BasePage {
  readonly path = '/cart.html';

  readonly cartItems: Locator;
  readonly itemNames: Locator;
  readonly checkoutButton: Locator;
  readonly continueButton: Locator;

  constructor(page: Page) {
    super(page);
    this.cartItems = page.locator('.cart_item');
    this.itemNames = page.locator('.inventory_item_name');
    this.checkoutButton = page.locator('#checkout');
    this.continueButton = page.locator('#continue-shopping');
  }

  async itemNameList(): Promise<string[]> {
    return (await this.itemNames.allTextContents()).map((s) => s.trim());
  }

  async itemCount(): Promise<number> {
    return await this.cartItems.count();
  }

  async removeItem(itemName: string): Promise<void> {
    const row = this.cartItems.filter({ hasText: itemName });
    await row.getByRole('button', { name: /remove/i }).click();
  }

  async checkout(): Promise<void> {
    await this.checkoutButton.click();
  }

  async continueShopping(): Promise<void> {
    await this.continueButton.click();
  }
}
