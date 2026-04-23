import { test, expect } from '@playwright/test';

const HEADERS = { 'x-api-key': 'reqres-free-v1' };

test.describe('reqres.in API @api @regression', () => {
  test('GET /api/users returns a paginated list @smoke', async ({ request }) => {
    const res = await request.get('/api/users?page=2', { headers: HEADERS });
    expect(res.status()).toBe(200);

    const body = await res.json();
    expect(body).toMatchObject({ page: 2, per_page: expect.any(Number) });
    expect(Array.isArray(body.data)).toBe(true);
    expect(body.data.length).toBeGreaterThan(0);
    for (const user of body.data) {
      expect(user).toEqual(
        expect.objectContaining({
          id: expect.any(Number),
          email: expect.stringMatching(/@reqres\.in$/),
          first_name: expect.any(String),
          last_name: expect.any(String),
          avatar: expect.stringMatching(/^https?:\/\//),
        }),
      );
    }
  });

  test('GET /api/users/:id returns a single user', async ({ request }) => {
    const res = await request.get('/api/users/2', { headers: HEADERS });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.data.id).toBe(2);
  });

  test('GET /api/users/:id with unknown id returns 404', async ({ request }) => {
    const res = await request.get('/api/users/23', { headers: HEADERS });
    expect(res.status()).toBe(404);
  });

  test('POST /api/users creates a user', async ({ request }) => {
    const payload = { name: 'ada', job: 'engineer' };
    const res = await request.post('/api/users', { headers: HEADERS, data: payload });
    expect(res.status()).toBe(201);

    const body = await res.json();
    expect(body).toMatchObject(payload);
    expect(body.id).toBeDefined();
    expect(body.createdAt).toBeDefined();
  });

  test('PUT /api/users/:id updates a user', async ({ request }) => {
    const payload = { name: 'ada', job: 'staff engineer' };
    const res = await request.put('/api/users/2', { headers: HEADERS, data: payload });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toMatchObject(payload);
    expect(body.updatedAt).toBeDefined();
  });

  test('DELETE /api/users/:id returns 204', async ({ request }) => {
    const res = await request.delete('/api/users/2', { headers: HEADERS });
    expect(res.status()).toBe(204);
  });

  test('POST /api/login without password returns 400', async ({ request }) => {
    const res = await request.post('/api/login', {
      headers: HEADERS,
      data: { email: 'peter@klaven' },
    });
    expect(res.status()).toBe(400);
    const body = await res.json();
    expect(body.error).toMatch(/missing password/i);
  });
});
