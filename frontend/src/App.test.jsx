import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, test, expect, vi } from 'vitest';
import Home from './components/Home';

beforeEach(() => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve([]),
    })
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

test('renders the dashboard screen', async () => {
  render(<Home />);

  expect(screen.getByRole('heading', { name: /YalaharBot/i })).toBeInTheDocument();
  expect(screen.getByText(/Automation Modules/i)).toBeInTheDocument();
  expect(screen.getByText(/Command Matrix/i)).toBeInTheDocument();

  await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(5));
});
