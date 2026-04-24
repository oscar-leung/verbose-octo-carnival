import { test, expect } from '../fixtures/todo.fixture.js';
import { SAMPLES } from '../data/samples.js';

test.describe('Add todos @regression', () => {
  test('adds a single todo @smoke', async ({ todoPage }) => {
    await todoPage.add(SAMPLES.single);
    await expect(todoPage.items).toHaveCount(1);
    await expect(todoPage.items.first()).toHaveText(SAMPLES.single);
  });

  test('adds multiple todos', async ({ todoPage }) => {
    await todoPage.addMany(SAMPLES.three);
    await expect(todoPage.items).toHaveCount(SAMPLES.three.length);
    await expect(todoPage.items).toHaveText([...SAMPLES.three]);
  });

  test('clears the input after adding', async ({ todoPage }) => {
    await todoPage.add(SAMPLES.single);
    await expect(todoPage.input).toHaveValue('');
  });

  test('counter shows remaining items', async ({ seededTodoPage }) => {
    await expect(seededTodoPage.counter).toContainText('3');
  });
});
