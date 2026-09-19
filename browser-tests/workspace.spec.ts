import { test, expect } from '@playwright/test';

test('landing page opens the local workspace with a healthy backend', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /keep your direction/i })).toBeVisible();
  await page.getByRole('link', { name: /enter your workspace/i }).click();
  await expect(page).toHaveURL(/\/app$/);
  const health = await page.request.get('/api/v1/health');
  expect(health.ok()).toBeTruthy();
  expect((await health.json()).status).toBe('ok');
});
