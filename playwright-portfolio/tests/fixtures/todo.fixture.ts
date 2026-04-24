import { test as base, expect } from '@playwright/test';
import { TodoPage } from '../pages/todo.page.js';

type Fixtures = {
  todoPage: TodoPage;
  seededTodoPage: TodoPage;
};

export const test = base.extend<Fixtures>({
  todoPage: async ({ page }, use) => {
    const todoPage = new TodoPage(page);
    await todoPage.goto();
    await use(todoPage);
  },
  seededTodoPage: async ({ todoPage }, use) => {
    await todoPage.addMany(['buy milk', 'write tests', 'ship it']);
    await use(todoPage);
  },
});

export { expect };
