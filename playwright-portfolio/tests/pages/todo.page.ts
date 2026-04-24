import type { Locator, Page } from '@playwright/test';
import { BasePage } from './base.page.js';

export type Filter = 'All' | 'Active' | 'Completed';

export class TodoPage extends BasePage {
  readonly path = '/todomvc';

  readonly input: Locator;
  readonly items: Locator;
  readonly toggleAll: Locator;
  readonly clearCompleted: Locator;
  readonly counter: Locator;

  constructor(page: Page) {
    super(page);
    this.input = page.getByPlaceholder('What needs to be done?');
    this.items = page.getByTestId('todo-item');
    this.toggleAll = page.getByLabel('Mark all as complete');
    this.clearCompleted = page.getByRole('button', { name: /clear completed/i });
    this.counter = page.locator('.todo-count');
  }

  async add(text: string): Promise<void> {
    await this.input.fill(text);
    await this.input.press('Enter');
  }

  async addMany(texts: readonly string[]): Promise<void> {
    for (const t of texts) await this.add(t);
  }

  item(text: string): Locator {
    return this.items.filter({ hasText: text });
  }

  async toggle(text: string): Promise<void> {
    await this.item(text).getByRole('checkbox').check();
  }

  async untoggle(text: string): Promise<void> {
    await this.item(text).getByRole('checkbox').uncheck();
  }

  async remove(text: string): Promise<void> {
    const row = this.item(text);
    await row.hover();
    await row.getByRole('button', { name: /delete/i }).click();
  }

  async edit(oldText: string, newText: string): Promise<void> {
    const row = this.item(oldText);
    await row.getByText(oldText).dblclick();
    const editBox = row.locator('.edit');
    await editBox.fill(newText);
    await editBox.press('Enter');
  }

  async filter(name: Filter): Promise<void> {
    await this.page.getByRole('link', { name, exact: true }).click();
  }

  async texts(): Promise<string[]> {
    return (await this.items.allTextContents()).map((s) => s.trim());
  }

  async completedCount(): Promise<number> {
    return this.items.locator('.completed').count();
  }

  async counterText(): Promise<string> {
    return (await this.counter.textContent())?.trim() ?? '';
  }
}
