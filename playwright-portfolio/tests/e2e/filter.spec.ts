import { test, expect } from '../fixtures/todo.fixture.js';
import { SAMPLES } from '../data/samples.js';

test.describe('Filter @regression', () => {
  test('Active filter hides completed @smoke', async ({ seededTodoPage }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await seededTodoPage.filter('Active');
    await expect(seededTodoPage.items).toHaveCount(2);
    await expect(seededTodoPage.items).toHaveText([SAMPLES.three[1], SAMPLES.three[2]]);
  });

  test('Completed filter shows only completed', async ({ seededTodoPage }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await seededTodoPage.toggle(SAMPLES.three[2]);
    await seededTodoPage.filter('Completed');
    await expect(seededTodoPage.items).toHaveCount(2);
  });

  test('All filter restores everything', async ({ seededTodoPage }) => {
    await seededTodoPage.toggle(SAMPLES.three[0]);
    await seededTodoPage.filter('Completed');
    await seededTodoPage.filter('All');
    await expect(seededTodoPage.items).toHaveCount(3);
  });
});
