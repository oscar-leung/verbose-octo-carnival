import { test, expect } from '../fixtures/todo.fixture.js';
import { SAMPLES } from '../data/samples.js';

test.describe('Edit + delete @regression', () => {
  test('double-click enables editing and saves on Enter', async ({ seededTodoPage }) => {
    await seededTodoPage.edit(SAMPLES.three[1], 'updated todo text');
    await expect(seededTodoPage.items).toHaveText([
      SAMPLES.three[0],
      'updated todo text',
      SAMPLES.three[2],
    ]);
  });

  test('delete button removes an item @smoke', async ({ seededTodoPage }) => {
    await seededTodoPage.remove(SAMPLES.three[1]);
    await expect(seededTodoPage.items).toHaveCount(2);
    await expect(seededTodoPage.items).toHaveText([SAMPLES.three[0], SAMPLES.three[2]]);
  });

  test('deleting all items hides the main section', async ({ seededTodoPage, page }) => {
    for (const t of SAMPLES.three) await seededTodoPage.remove(t);
    await expect(seededTodoPage.items).toHaveCount(0);
    await expect(page.locator('.main')).toBeHidden();
  });
});
