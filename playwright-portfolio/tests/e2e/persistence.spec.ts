import { test, expect } from '../fixtures/todo.fixture.js';
import { SAMPLES } from '../data/samples.js';

test.describe('Persistence + responsive @regression', () => {
  test('todos survive a reload (localStorage)', async ({ seededTodoPage, page }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await page.reload();
    await expect(seededTodoPage.items).toHaveCount(3);
    await expect(seededTodoPage.item(SAMPLES.three[0])).toHaveClass(/completed/);
  });

  test('input + list render on a small viewport @mobile', async ({ todoPage }) => {
    await todoPage.add(SAMPLES.single);
    await expect(todoPage.input).toBeVisible();
    await expect(todoPage.items).toHaveCount(1);
    await expect(todoPage.items.first()).toHaveText(SAMPLES.single);
  });
});
