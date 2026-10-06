import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, test, expect, vi } from 'vitest';
import EnemyDashboard, { formatOnlineDuration } from './components/EnemyDashboard';
import { groupEnemies } from './components/enemyGrouping';

function response(payload, ok = true) {
  return Promise.resolve({ ok, status: ok ? 200 : 502, json: () => Promise.resolve(payload) });
}

function mockMonitor(statusPayload, observations = [], mutation) {
  global.fetch = vi.fn((url, options = {}) => {
    if (url === '/api/site-access/status/') return response({ authenticated: true });
    if (url === '/api/enemy-list/observations/' && !options.method) return response(observations);
    if (url === '/api/enemy-list/observations/' && options.method) return mutation(url, options);
    if (url === '/api/monitors/status/') return response({
      world: statusPayload.world,
      monitors: {
        enemy: { online_count: statusPayload.enemy_online_count, players: statusPayload.enemies, guilds: statusPayload.guilds },
        friend: { online_count: 0, players: [], guilds: [{ name: 'Unfallen', error: null }] },
      },
    });
    throw new Error(`Unexpected request: ${url}`);
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('enemy grouping', () => {
  test('groups known, promoted, monk, and future vocations safely', () => {
    const grouped = groupEnemies([
      { name: 'Knight', level: 10, vocation: 'Elite Knight' },
      { name: 'Paladin', level: 20, vocation: 'Royal Paladin' },
      { name: 'Sorcerer', level: 30, vocation: 'Master Sorcerer' },
      { name: 'Druid', level: 40, vocation: 'Elder Druid' },
      { name: 'Monk', level: 50, vocation: 'Exalted Monk' },
      { name: 'Unknown', level: 60, vocation: 'Astral Ranger' },
    ]);

    expect(grouped.knights.map((enemy) => enemy.name)).toEqual(['Knight']);
    expect(grouped.paladins.map((enemy) => enemy.name)).toEqual(['Paladin']);
    expect(grouped.sorcerers.map((enemy) => enemy.name)).toEqual(['Sorcerer']);
    expect(grouped.druids.map((enemy) => enemy.name)).toEqual(['Druid']);
    expect(grouped.monks.map((enemy) => enemy.name)).toEqual(['Monk']);
    expect(grouped.other.map((enemy) => enemy.name)).toEqual(['Unknown']);
  });

  test('sorts each vocation group by level descending', () => {
    const grouped = groupEnemies([
      { name: 'Lower Knight', level: 701, vocation: 'Knight' },
      { name: 'Higher Knight', level: 1050, vocation: 'Elite Knight' },
      { name: 'Middle Knight', level: 892, vocation: 'Knight' },
    ]);

    expect(grouped.knights.map((enemy) => enemy.name)).toEqual([
      'Higher Knight', 'Middle Knight', 'Lower Knight',
    ]);
  });
});

test('observed online duration increases compactly from its first timestamp', () => {
  const started = '2026-01-01T01:00:00Z';
  expect(formatOnlineDuration(started, new Date('2026-01-01T01:00:35Z').getTime())).toBe('35s');
  expect(formatOnlineDuration(started, new Date('2026-01-01T01:01:00Z').getTime())).toBe('1m');
  expect(formatOnlineDuration(started, new Date('2026-01-01T02:05:00Z').getTime())).toBe('1h 05m');
});

test('renders grouped live enemies from the existing Django API', async () => {
  mockMonitor({
    world: 'Monstera', world_online_count: 42, enemy_online_count: 2,
    enemies: [
      { name: 'Monk Enemy', level: 900, vocation: 'Exalted Monk', guilds: ['Watch The Throne'] },
      { name: 'Knight Enemy', level: 1000, vocation: 'Elite Knight', guilds: ['Watch The Throne'] },
    ], guilds: [],
  });

  render(<EnemyDashboard />);

  expect(await screen.findByRole('heading', { name: /Enemy Monitor/i })).toBeInTheDocument();
  expect(screen.getByText(/Auto 10s/i)).toBeInTheDocument();
  expect(await screen.findByText('Monk Enemy')).toBeInTheDocument();
  const enemyMonitor = within(screen.getByRole('region', { name: 'Enemy monitor' }));
  const monks = within(enemyMonitor.getByRole('heading', { name: /Monks/i }).closest('section'));
  expect(monks.queryByText('Exalted Monk')).not.toBeInTheDocument();
  expect(monks.getByText('Level')).toBeInTheDocument();
  expect(monks.getByText('Name')).toBeInTheDocument();
  expect(monks.getByText('Online')).toBeInTheDocument();
  expect(monks.getByText('Observations')).toBeInTheDocument();
  expect(screen.getByText('Knight Enemy')).toBeInTheDocument();
  expect(screen.queryByText(/Monitor configuration/i)).not.toBeInTheDocument();
  expect(screen.queryByRole('textbox', { name: /Tibia world/i })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Add' })).not.toBeInTheDocument();
});

test('keeps the previous successful results when a refresh temporarily fails', async () => {
  global.fetch = vi.fn((url) => {
    if (url === '/api/site-access/status/') return response({ authenticated: true });
    if (url === '/api/enemy-list/observations/') return response([]);
    return response({ world: 'Monstera', monitors: {
      enemy: { online_count: 1, players: [{ name: 'Persistent Enemy', level: 800, vocation: 'Knight', guilds: ['Watch The Throne'] }], guilds: [] },
      friend: { online_count: 0, players: [], guilds: [] },
    } });
  });

  render(<EnemyDashboard />);
  expect(await screen.findByText('Persistent Enemy')).toBeInTheDocument();

  global.fetch.mockImplementation((url) => url === '/api/monitors/status/'
    ? response({ error: 'Tibia.com unavailable' }, false) : response([]));
  fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));

  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Live refresh failed'));
  expect(screen.getByText('Persistent Enemy')).toBeInTheDocument();
});

test('renders a separate Unfallen friend monitor with compact grouped and sorted tables', async () => {
  global.fetch = vi.fn((url) => {
    if (url === '/api/site-access/status/') return response({ authenticated: true });
    if (url === '/api/enemy-list/observations/') return response([{ character_name: 'Friendly Knight', observation: 'Main EK' }]);
    if (url === '/api/monitors/status/') return response({
      world: 'Monstera', monitors: {
        enemy: { online_count: 1, players: [{ name: 'Enemy Knight', level: 700, vocation: 'Elite Knight', online_since: new Date().toISOString(), guilds: ['Watch The Throne'] }], guilds: [] },
        friend: { online_count: 2, players: [
          { name: 'Lower Friend', level: 800, vocation: 'Elite Knight', online_since: new Date().toISOString(), guilds: ['Unfallen'] },
          { name: 'Friendly Knight', level: 1200, vocation: 'Elite Knight', online_since: new Date().toISOString(), guilds: ['Unfallen'] },
        ], guilds: [] },
      },
    });
    throw new Error(`Unexpected request: ${url}`);
  });

  render(<EnemyDashboard />);
  const friend = within(await screen.findByRole('region', { name: 'Friend monitor' }));
  expect(friend.getByRole('heading', { name: /Friend Monitor/i })).toBeInTheDocument();
  expect(friend.getByText('Unfallen')).toBeInTheDocument();
  const knights = within((await friend.findByRole('heading', { name: /Knights/i })).closest('section'));
  expect(knights.getByText('Level')).toBeInTheDocument();
  expect(knights.getByText('Name')).toBeInTheDocument();
  expect(knights.getByText('Online')).toBeInTheDocument();
  expect(knights.getByText('Observations')).toBeInTheDocument();
  expect(knights.getAllByRole('button').filter((button) => ['Friendly Knight', 'Lower Friend'].includes(button.textContent)).map((button) => button.textContent)).toEqual(['Friendly Knight', 'Lower Friend']);
  expect(knights.getByRole('button', { name: 'Observation for Friendly Knight' })).toHaveTextContent('Main EK');
  expect(friend.queryByText('Enemy Knight')).not.toBeInTheDocument();
});

test('friend name copies Exiva and friend observation opens without copying', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
  global.fetch = vi.fn((url) => {
    if (url === '/api/site-access/status/') return response({ authenticated: true });
    if (url === '/api/enemy-list/observations/') return response([{ character_name: 'Friendly Knight', observation: 'Main EK' }]);
    return response({ world: 'Monstera', monitors: {
      enemy: { online_count: 0, players: [], guilds: [] },
      friend: { online_count: 1, players: [{ name: 'Friendly Knight', level: 1200, vocation: 'Elite Knight', online_since: new Date().toISOString(), guilds: ['Unfallen'] }], guilds: [] },
    } });
  });

  render(<EnemyDashboard />);
  const friend = within(await screen.findByRole('region', { name: 'Friend monitor' }));
  fireEvent.click(friend.getByRole('button', { name: 'Friendly Knight' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith('Exiva "Friendly Knight"'));
  fireEvent.click(friend.getByRole('button', { name: 'Observation for Friendly Knight' }));
  expect(screen.getByRole('dialog')).toHaveTextContent('Main EK');
  expect(writeText).toHaveBeenCalledTimes(1);
});

test('site access requires backend login and compact logout returns to password screen', async () => {
  global.fetch = vi.fn((url, options = {}) => {
    if (url === '/api/site-access/status/') return response({ authenticated: false });
    if (url === '/api/site-access/login/') {
      const body = JSON.parse(options.body);
      return body.password === 'site password'
        ? response({ authenticated: true }) : response({ error: 'Invalid password.' }, false);
    }
    if (url === '/api/site-access/logout/') return response({ authenticated: false });
    if (url === '/api/enemy-list/observations/') return response([]);
    if (url === '/api/monitors/status/') return response({
      world: 'Monstera', monitors: {
        enemy: { online_count: 0, players: [], guilds: [] },
        friend: { online_count: 0, players: [], guilds: [] },
      },
    });
    throw new Error(`Unexpected request: ${url}`);
  });

  render(<EnemyDashboard />);
  expect(await screen.findByRole('heading', { name: 'Tibia War Monitor' })).toBeInTheDocument();
  expect(screen.queryByRole('region', { name: 'Enemy monitor' })).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
  fireEvent.click(screen.getByRole('button', { name: 'Enter' }));
  expect(await screen.findByText('Invalid password.')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'site password' } });
  fireEvent.click(screen.getByRole('button', { name: 'Enter' }));
  expect(await screen.findByRole('region', { name: 'Enemy monitor' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Logout' }));
  expect(await screen.findByRole('heading', { name: 'Tibia War Monitor' })).toBeInTheDocument();
});

test('copies exact Exiva commands for different characters and tolerates clipboard failure', async () => {
  const writeText = vi.fn().mockResolvedValueOnce(undefined).mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error('denied'));
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
  mockMonitor({
      world: 'Monstera', enemy_online_count: 2,
      enemies: [
        { name: 'Mago Malvado', level: 900, vocation: 'Master Sorcerer', guilds: ['Enemy Guild'], online_since: new Date().toISOString() },
        { name: 'Knight Enemy', level: 800, vocation: 'Elite Knight', guilds: ['Enemy Guild'], online_since: new Date().toISOString() },
      ], guilds: [],
    });

  render(<EnemyDashboard />);
  fireEvent.click(await screen.findByRole('button', { name: 'Mago Malvado' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith('Exiva "Mago Malvado"'));
  fireEvent.click(screen.getByRole('button', { name: 'Knight Enemy' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith('Exiva "Knight Enemy"'));
  fireEvent.click(screen.getByRole('button', { name: 'Mago Malvado' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledTimes(3));
  expect(screen.getByText('Mago Malvado')).toBeInTheDocument();
});

test('shows observations as compact cells and keeps name and observation clicks separate', async () => {
  const longNote = 'Main EK, usually plays together with the main ED and is priority target';
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
  mockMonitor({
    world: 'Monstera', enemy_online_count: 2,
    enemies: [
      { name: 'Mago Malvado', level: 900, vocation: 'Master Sorcerer', guilds: ['Watch The Throne'], online_since: new Date().toISOString() },
      { name: 'No Note', level: 800, vocation: 'Master Sorcerer', guilds: ['Watch The Throne'], online_since: new Date().toISOString() },
    ], guilds: [],
  }, [{ character_name: 'mago malvado', observation: longNote }]);

  render(<EnemyDashboard />);
  const noteCell = await screen.findByRole('button', { name: 'Observation for Mago Malvado' });
  expect(noteCell).toHaveTextContent(longNote);
  expect(noteCell).toHaveAttribute('title', longNote);
  expect(noteCell).toHaveClass('truncate');
  expect(noteCell.parentElement).toHaveClass('h-[22px]');
  expect(screen.getByRole('button', { name: 'Observation for No Note' })).toHaveTextContent('—');

  fireEvent.click(noteCell);
  expect(screen.getByRole('dialog')).toHaveTextContent(longNote);
  expect(writeText).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Close observation' }));
  fireEvent.click(screen.getByRole('button', { name: 'Mago Malvado' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith('Exiva "Mago Malvado"'));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

test('successful and failed observation edits update safely without losing the live list', async () => {
  let attempts = 0;
  mockMonitor({
    world: 'Monstera', enemy_online_count: 1,
    enemies: [{ name: 'Mago Malvado', level: 900, vocation: 'Master Sorcerer', guilds: ['Watch The Throne'], online_since: new Date().toISOString() }],
    guilds: [],
  }, [{ character_name: 'Mago Malvado', observation: 'Original' }], (_url, options) => {
    attempts += 1;
    const body = JSON.parse(options.body);
    return attempts === 1
      ? response({ error: 'Invalid password.' }, false)
      : response({ character_name: body.character_name, observation: body.observation });
  });

  render(<EnemyDashboard />);
  fireEvent.click(await screen.findByRole('button', { name: 'Observation for Mago Malvado' }));
  fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
  fireEvent.change(screen.getByLabelText('Observation'), { target: { value: 'Should not appear' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));
  expect(await screen.findByText('Invalid password.')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Observation for Mago Malvado' })).toHaveTextContent('Original');

  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct' } });
  fireEvent.change(screen.getByLabelText('Observation'), { target: { value: 'Updated immediately' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Observation for Mago Malvado' })).toHaveTextContent('Updated immediately'));
  expect(screen.getByRole('button', { name: 'Mago Malvado' })).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Observation for Mago Malvado' })).toHaveTextContent('Updated immediately'));
});
