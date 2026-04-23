import type { Locator, Page } from '@playwright/test';
import { BasePage } from './base.page.js';

export class CheckoutPage extends BasePage {
  readonly path = '/checkout-step-one.html';

  readonly firstName: Locator;
  readonly lastName: Locator;
  readonly postalCode: Locator;
  readonly continueButton: Locator;
  readonly finishButton: Locator;
  readonly errorMessage: Locator;
  readonly successHeader: Locator;
  readonly subtotalLabel: Locator;
  readonly taxLabel: Locator;
  readonly totalLabel: Locator;

  constructor(page: Page) {
    super(page);
    this.firstName = page.locator('#first-name');
    this.lastName = page.locator('#last-name');
    this.postalCode = page.locator('#postal-code');
    this.continueButton = page.locator('#continue');
    this.finishButton = page.locator('#finish');
    this.errorMessage = page.locator('[data-test="error"]');
    this.successHeader = page.locator('.complete-header');
    this.subtotalLabel = page.locator('.summary_subtotal_label');
    this.taxLabel = page.locator('.summary_tax_label');
    this.totalLabel = page.locator('.summary_total_label');
  }

  async fillInfo(first: string, last: string, zip: string): Promise<void> {
    await this.firstName.fill(first);
    await this.lastName.fill(last);
    await this.postalCode.fill(zip);
  }

  async submitInfo(): Promise<void> {
    await this.continueButton.click();
  }

  async finish(): Promise<void> {
    await this.finishButton.click();
  }

  private async parseMoney(locator: Locator, prefix: string): Promise<number> {
    const text = (await locator.textContent()) ?? '';
    const cleaned = text.replace(prefix, '').replace('$', '').trim();
    return parseFloat(cleaned);
  }

  async subtotal(): Promise<number> {
    return this.parseMoney(this.subtotalLabel, 'Item total: ');
  }

  async tax(): Promise<number> {
    return this.parseMoney(this.taxLabel, 'Tax: ');
  }

  async total(): Promise<number> {
    return this.parseMoney(this.totalLabel, 'Total: ');
  }
}
