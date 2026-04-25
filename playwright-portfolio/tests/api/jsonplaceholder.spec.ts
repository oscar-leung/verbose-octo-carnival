import { test, expect } from '@playwright/test';
import { userSchema, postSchema } from './schema.js';

test.describe('JSONPlaceholder API @api @regression', () => {
  test('GET /users returns a list matching the user schema @smoke', async ({ request }) => {
    const res = await request.get('/users');
    expect(res.status()).toBe(200);

    const users = await res.json();
    expect(users.length).toBeGreaterThan(0);
    for (const user of users) expect(user).toEqual(userSchema);
  });

  test('GET /users/:id returns a single user', async ({ request }) => {
    const res = await request.get('/users/1');
    expect(res.status()).toBe(200);

    const user = await res.json();
    expect(user).toEqual(userSchema);
    expect(user.id).toBe(1);
  });

  test('GET /users/:id with unknown id returns 404', async ({ request }) => {
    const res = await request.get('/users/99999');
    expect(res.status()).toBe(404);
  });

  test('GET /posts?userId=1 filters by user', async ({ request }) => {
    const res = await request.get('/posts?userId=1');
    expect(res.status()).toBe(200);

    const posts = await res.json();
    expect(posts.length).toBeGreaterThan(0);
    for (const post of posts) {
      expect(post).toEqual(postSchema);
      expect(post.userId).toBe(1);
    }
  });

  test('POST /posts creates a post', async ({ request }) => {
    const payload = { title: 'sdet-portfolio', body: 'created by playwright', userId: 1 };
    const res = await request.post('/posts', { data: payload });
    expect(res.status()).toBe(201);

    const body = await res.json();
    expect(body).toMatchObject(payload);
    expect(body.id).toEqual(expect.any(Number));
  });

  test('PUT /posts/:id replaces a post', async ({ request }) => {
    const payload = { id: 1, title: 'updated', body: 'replaced body', userId: 1 };
    const res = await request.put('/posts/1', { data: payload });
    expect(res.status()).toBe(200);
    expect(await res.json()).toMatchObject(payload);
  });

  test('DELETE /posts/:id returns 200', async ({ request }) => {
    const res = await request.delete('/posts/1');
    expect(res.status()).toBe(200);
  });
});
