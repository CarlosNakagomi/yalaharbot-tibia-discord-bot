'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { apiFetch } from '../api';

async function request(url, options) {
  const response = await apiFetch(url, options);
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || payload.name?.[0] || 'Request failed.');
  return payload;
}

function EnemyRow({ enemy }) {
  return <div className="grid gap-3 border border-red-900/80 bg-[#160d0d] p-4 sm:grid-cols-[1fr_auto_auto] sm:items-center">
    <div><p className="text-lg font-black text-white">{enemy.name}</p><p className="mt-1 text-xs uppercase tracking-wider text-red-300">{enemy.guilds.join(' · ')}</p></div>
    <p className="font-mono text-sm text-stone-300">{enemy.vocation}</p><p className="font-mono text-xl font-black text-amber-300">LV {enemy.level}</p>
  </div>;
}

export default function EnemyList() {
  const [world, setWorld] = useState('');
  const [savedWorld, setSavedWorld] = useState('');
  const [guildName, setGuildName] = useState('');
  const [guilds, setGuilds] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');

  const loadSetup = useCallback(async () => {
    try {
      const [config, payload] = await Promise.all([request('/api/enemy-list/config/'), request('/api/enemy-guilds/')]);
      const rows = Array.isArray(payload) ? payload : payload.results || [];
      setWorld(config.selected_world || ''); setSavedWorld(config.selected_world || ''); setGuilds(rows); setError('');
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  }, []);
  useEffect(() => { loadSetup(); }, [loadSetup]);

  async function saveWorld(event) {
    event.preventDefault();
    try {
      const config = await request('/api/enemy-list/config/', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ selected_world: world }) });
      setSavedWorld(config.selected_world); setStatus(null); setError('');
    } catch (err) { setError(err.message); }
  }
  async function addGuild(event) {
    event.preventDefault();
    try {
      const guild = await request('/api/enemy-guilds/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: guildName }) });
      setGuilds((current) => [...current, guild].sort((a, b) => a.name.localeCompare(b.name))); setGuildName(''); setStatus(null); setError('');
    } catch (err) { setError(err.message); }
  }
  async function removeGuild(guild) {
    try {
      await request(`/api/enemy-guilds/${guild.id}/`, { method: 'DELETE' });
      setGuilds((current) => current.filter((item) => item.id !== guild.id)); setStatus(null); setError('');
    } catch (err) { setError(err.message); }
  }
  async function scan() {
    setScanning(true);
    try { setStatus(await request('/api/enemy-list/status/')); setError(''); }
    catch (err) { setError(err.message); } finally { setScanning(false); }
  }

  return <main className="min-h-screen bg-[#090909] text-stone-100"><div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-12">
    <header className="border-b border-red-900 pb-8">
      <p className="font-mono text-xs font-bold uppercase tracking-[0.35em] text-red-400">Tibia intelligence</p>
      <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><h1 className="text-4xl font-black uppercase tracking-tight text-white sm:text-6xl">Enemy List</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-stone-400">Monitor enemy guild rosters against the live online list for your world.</p></div>
      <button onClick={scan} disabled={scanning || !savedWorld || !guilds.length} className="border border-red-500 bg-red-600 px-6 py-3 font-black uppercase text-white disabled:cursor-not-allowed disabled:border-stone-700 disabled:bg-stone-800 disabled:text-stone-500">{scanning ? 'Scanning Tibia…' : 'Refresh enemies'}</button></div>
    </header>
    {error && <div role="alert" className="mt-6 border border-red-700 bg-red-950/60 p-4 text-sm text-red-100">{error}</div>}
    <section className="mt-6 grid gap-5 lg:grid-cols-2">
      <form onSubmit={saveWorld} className="border border-stone-800 bg-stone-950 p-5"><p className="font-mono text-xs uppercase text-stone-500">01 / World</p><h2 className="mt-1 text-xl font-black uppercase">Configure world</h2><div className="mt-4 flex gap-2"><input aria-label="Tibia world" value={world} onChange={(e) => setWorld(e.target.value)} placeholder="e.g. Antica" required className="min-w-0 flex-1 border border-stone-700 bg-black px-4 py-3 outline-none focus:border-red-500"/><button className="border border-stone-600 px-4 py-3 font-bold uppercase hover:border-white">Save</button></div><p className="mt-3 text-xs text-stone-500">Active world: <span className="text-stone-200">{savedWorld || 'Not configured'}</span></p></form>
      <div className="border border-stone-800 bg-stone-950 p-5"><p className="font-mono text-xs uppercase text-stone-500">02 / Targets</p><h2 className="mt-1 text-xl font-black uppercase">Enemy guilds</h2><form onSubmit={addGuild} className="mt-4 flex gap-2"><input aria-label="Enemy guild" value={guildName} onChange={(e) => setGuildName(e.target.value)} placeholder="Guild name" required className="min-w-0 flex-1 border border-stone-700 bg-black px-4 py-3 outline-none focus:border-red-500"/><button className="border border-red-700 px-4 py-3 font-bold uppercase text-red-300 hover:bg-red-950">Add</button></form><div className="mt-3 flex flex-wrap gap-2">{guilds.map((guild) => <button key={guild.id} onClick={() => removeGuild(guild)} title={`Remove ${guild.name}`} className="border border-stone-700 bg-stone-900 px-3 py-2 text-xs hover:border-red-500 hover:text-red-300">{guild.name} ×</button>)}{!loading && !guilds.length && <p className="text-xs text-stone-500">Add at least one guild to begin scanning.</p>}</div></div>
    </section>
    <section className="mt-6 border border-stone-800 bg-stone-950 p-5"><div className="flex flex-wrap items-end justify-between gap-4 border-b border-stone-800 pb-4"><div><p className="font-mono text-xs uppercase text-stone-500">03 / Live results</p><h2 className="mt-1 text-2xl font-black uppercase">Enemies online</h2></div>{status && <div className="flex gap-6 font-mono text-xs uppercase text-stone-400"><span><b className="text-xl text-white">{status.enemy_online_count}</b> enemies</span><span><b className="text-xl text-white">{status.world_online_count}</b> online</span></div>}</div>
      <div className="mt-4 grid gap-3">{status?.enemies.map((enemy) => <EnemyRow key={enemy.name} enemy={enemy}/>)}{status && !status.enemies.length && <p className="border border-dashed border-stone-700 p-8 text-center text-sm text-stone-400">No configured enemies are online on {status.world}.</p>}{!status && <p className="border border-dashed border-stone-800 p-8 text-center text-sm text-stone-500">Configure a world and enemy guilds, then refresh the live scan.</p>}</div>
      {status?.guilds.some((guild) => guild.error) && <div className="mt-5 border-t border-stone-800 pt-4 text-xs text-amber-300">Some guilds could not be loaded: {status.guilds.filter((guild) => guild.error).map((guild) => guild.name).join(', ')}</div>}
    </section>
  </div></main>;
}
