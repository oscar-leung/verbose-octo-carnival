import { expect } from '@playwright/test';

export const userSchema = expect.objectContaining({
  id: expect.any(Number),
  name: expect.any(String),
  username: expect.any(String),
  email: expect.stringMatching(/@/),
});

export const postSchema = expect.objectContaining({
  id: expect.any(Number),
  userId: expect.any(Number),
  title: expect.any(String),
  body: expect.any(String),
});
