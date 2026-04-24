import { test, expect } from '../fixtures/todo.fixture.js';
import { SAMPLES } from '../data/samples.js';

test.describe('Complete + clear @regression', () => {
  test('toggling a todo marks it completed @smoke', async ({ seededTodoPage }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await expect(seededTodoPage.item(SAMPLES.three[0])).toHaveClass(/completed/);
    await expect(seededTodoPage.counter).toContainText('2');
  });

  test('untoggling restores a todo to active', async ({ seededTodoPage }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await seededTodoPage.untoggle(SAMPLES.three[0]);
    await expect(seededTodoPage.item(SAMPLES.three[0])).not.toHaveClass(/completed/);
    await expect(seededTodoPage.counter).toContainText('3');
  });

  test('toggle-all marks every todo completed', async ({ seededTodoPage }) => {
    await seededTodoPage.toggleAll.check();
    for (const t of SAMPLES.three) {
      await expect(seededTodoPage.item(t)).toHaveClass(/completed/);
    }
    await expect(seededTodoPage.counter).toContainText('0');
  });

  test('clear-completed removes only completed items', async ({ seededTodoPage }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await seededTodoPage.toggle(SAMPLES.three[2]);
    await seededTodoPage.clearCompleted.click();
    await expect(seededTodoPage.items).toHaveCount(1);
    await expect(seededTodoPage.items.first()).toHaveText(SAMPLES.three[1]);
  });
});
