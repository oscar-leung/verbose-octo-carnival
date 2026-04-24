import { test, expect } from '@playwright/test';

test.describe('JSONPlaceholder API @api @regression', () => {
  test('GET /users returns a list of users @smoke', async ({ request }) => {
    const res = await request.get('/users');
    expect(res.status()).toBe(200);

    const users = await res.json();
    expect(Array.isArray(users)).toBe(true);
    expect(users.length).toBeGreaterThan(0);
    for (const user of users) {
      expect(user).toEqual(
        expect.objectContaining({
          id: expect.any(Number),
          name: expect.any(String),
          email: expect.stringMatching(/@/),
          username: expect.any(String),
        }),
      );
    }
  });

  test('GET /users/:id returns a single user', async ({ request }) => {
    const res = await request.get('/users/1');
    expect(res.status()).toBe(200);
    const user = await res.json();
    expect(user.id).toBe(1);
    expect(user).toEqual(
      expect.objectContaining({
        name: expect.any(String),
        email: expect.stringMatching(/@/),
      }),
    );
  });

  test('GET /users/:id with unknown id returns 404', async ({ request }) => {
    const res = await request.get('/users/99999');
    expect(res.status()).toBe(404);
  });

  test('GET /posts?userId=1 filters by user', async ({ request }) => {
    const res = await request.get('/posts?userId=1');
    expect(res.status()).toBe(200);
    const posts = await res.json();
    expect(Array.isArray(posts)).toBe(true);
    expect(posts.length).toBeGreaterThan(0);
    for (const post of posts) {
      expect(post.userId).toBe(1);
    }
  });

  test('POST /posts creates a post', async ({ request }) => {
    const payload = { title: 'sdet-portfolio', body: 'created by playwright test', userId: 1 };
    const res = await request.post('/posts', { data: payload });
    expect(res.status()).toBe(201);

    const body = await res.json();
    expect(body).toMatchObject(payload);
    expect(body.id).toBeDefined();
  });

  test('PUT /posts/:id replaces a post', async ({ request }) => {
    const payload = { id: 1, title: 'updated', body: 'replaced body', userId: 1 };
    const res = await request.put('/posts/1', { data: payload });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toMatchObject(payload);
  });

  test('DELETE /posts/:id returns 200', async ({ request }) => {
    const res = await request.delete('/posts/1');
    expect(res.status()).toBe(200);
  });
});
