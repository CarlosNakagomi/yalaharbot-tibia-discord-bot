'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { groupEnemies, VOCATION_GROUPS } from './enemyGrouping';
import { apiFetch } from '../api';

export const AUTO_REFRESH_MS = 10_000;

async function request(url, options) {
  const response = await apiFetch(url, options);
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || payload.name?.[0] || 'Request failed.');
  return payload;
}

export function formatOnlineDuration(onlineSince, now = Date.now()) {
  if (!onlineSince) return '—';
  const seconds = Math.max(0, Math.floor((now - new Date(onlineSince).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, '0')}m`;
}

const TABLE_COLUMNS = 'grid-cols-[3rem_minmax(0,1.15fr)_3.75rem_minmax(4rem,0.85fr)]';

function VocationColumn({ group, players, now, notes, copiedName, onCopy, onOpenNote }) {
  return <section className={`min-w-0 overflow-hidden border-t-2 border-x border-b bg-[#0d0d0e] ${group.accent}`}>
    <header className="flex h-7 items-center border-b border-stone-800 bg-white/[0.025] px-2">
      <h2 className="truncate text-[11px] font-black uppercase tracking-[0.08em] text-stone-300">{group.label} <span className="font-mono text-stone-500">({players.length})</span></h2>
    </header>
    <div className={`grid h-[18px] items-center gap-1 border-b border-stone-800 bg-black/30 px-1.5 font-mono text-[8px] font-bold uppercase tracking-wide text-stone-600 ${TABLE_COLUMNS}`}>
      <span className="text-right">Level</span><span>Name</span><span className="text-right">Online</span><span>Observations</span>
    </div>
    <div className="divide-y divide-stone-800/70">
      {players.map((enemy) => {
        const observation = notes[enemy.name.toLocaleLowerCase()]?.observation || '';
        return <div key={enemy.name} className={`grid h-[22px] items-center gap-1 px-1.5 font-mono text-xs leading-none ${TABLE_COLUMNS}`}>
        <span className={`text-right font-bold tabular-nums ${group.level}`}>{enemy.level}</span>
        <button type="button" onClick={() => onCopy(enemy.name)} className="min-w-0 cursor-pointer truncate text-left font-sans font-semibold text-stone-100 hover:text-red-200 hover:underline" title={`Copy Exiva &quot;${enemy.name}&quot;`}>{enemy.name}{copiedName === enemy.name && <span className="ml-1 text-[9px] font-normal text-emerald-400">Copied!</span>}</button>
        <span className="text-right text-[10px] tabular-nums text-stone-500" title="Continuously observed online duration">{formatOnlineDuration(enemy.online_since, now)}</span>
        <button type="button" onClick={() => onOpenNote(enemy)} aria-label={`Observation for ${enemy.name}`} title={observation || 'No observation'} className={`min-w-0 cursor-pointer truncate border-l border-stone-800 pl-1.5 text-left font-sans text-[10px] hover:bg-white/[0.04] hover:text-white ${observation ? 'text-stone-400' : 'text-stone-700'}`}>{observation || '—'}</button>
      </div>})}
    </div>
  </section>;
}

function MonitorSection({ type, guildName, world, monitor, now, notes, copiedName, onCopy, onOpenNote, toolbar }) {
  const grouped = useMemo(() => groupEnemies(monitor?.players), [monitor]);
  const visibleGroups = VOCATION_GROUPS.filter(({ key }) => key !== 'other' || grouped[key].length);
  const isFriend = type === 'friend';

  return <section aria-label={`${isFriend ? 'Friend' : 'Enemy'} monitor`} className={isFriend ? 'mt-3' : ''}>
    <header className={`flex min-h-11 flex-wrap items-center gap-x-3 gap-y-1 border bg-[#101011] px-3 py-1.5 shadow-lg ${isFriend ? 'border-emerald-900/70' : 'border-stone-800'}`}>
      <h1 className={`text-sm font-black uppercase tracking-[0.12em] ${isFriend ? 'text-emerald-300' : 'text-white'}`}>{isFriend ? 'Friend Monitor' : 'Enemy Monitor'}</h1>
      <span className="hidden h-4 w-px bg-stone-700 sm:block" aria-hidden="true" />
      <strong className="text-xs text-stone-300">{guildName}</strong>
      <span className={`font-mono text-xs font-black ${isFriend ? 'text-cyan-300' : 'text-red-300'}`}>{monitor?.online_count ?? '—'} ONLINE</span>
      <span className="text-[10px] uppercase text-stone-600">{world}</span>
      {toolbar}
    </header>
    <div className="mt-1 overflow-x-auto">
      {!monitor && <div className="border border-stone-800 bg-[#0d0d0e] py-8 text-center text-xs text-stone-500">Loading live {type} data…</div>}
      {monitor && !monitor.players.length && <div className="border border-stone-800 bg-[#0d0d0e] py-6 text-center text-xs text-stone-500">No {type}s currently online.</div>}
      {monitor?.players.length > 0 && <div className="grid min-w-[1100px] grid-cols-5 items-start gap-1">{visibleGroups.map((group) => <VocationColumn key={group.key} group={group} players={grouped[group.key]} now={now} notes={notes} copiedName={copiedName} onCopy={onCopy} onOpenNote={onOpenNote}/>)}</div>}
      {monitor?.guilds.some((guild) => guild.error) && <div className="mt-1 border border-amber-900/70 bg-amber-950/20 px-3 py-1.5 text-xs text-amber-300">Some guilds could not be loaded: {monitor.guilds.filter((guild) => guild.error).map((guild) => guild.name).join(', ')}</div>}
    </div>
  </section>;
}

export default function EnemyDashboard() {
  const [accessLoading, setAccessLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [accessPassword, setAccessPassword] = useState('');
  const [accessError, setAccessError] = useState('');
  const [status, setStatus] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [refreshWarning, setRefreshWarning] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [now, setNow] = useState(Date.now());
  const [notes, setNotes] = useState({});
  const [copiedName, setCopiedName] = useState('');
  const [selectedEnemy, setSelectedEnemy] = useState(null);
  const [editingNote, setEditingNote] = useState(false);
  const [noteDraft, setNoteDraft] = useState('');
  const [notePassword, setNotePassword] = useState('');
  const [noteMessage, setNoteMessage] = useState('');
  const [noteError, setNoteError] = useState('');
  const requestInFlight = useRef(false);
  const mounted = useRef(true);

  useEffect(() => () => { mounted.current = false; }, []);
  useEffect(() => {
    async function checkAccess() {
      try {
        const access = await request('/api/site-access/status/');
        if (mounted.current) setAuthenticated(Boolean(access.authenticated));
      } catch (_) {
        if (mounted.current) setAccessError('Unable to verify site access.');
      } finally {
        if (mounted.current) setAccessLoading(false);
      }
    }
    checkAccess();
  }, []);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!authenticated) return undefined;
    async function loadObservations() {
      try {
        const observations = await request('/api/enemy-list/observations/');
        if (!mounted.current) return;
        setNotes(Object.fromEntries(observations.map((item) => [item.character_name.toLocaleLowerCase(), item])));
      } catch (error) {
        if (mounted.current) setRefreshWarning(`Observations could not be loaded: ${error.message}`);
      }
    }
    loadObservations();
    return undefined;
  }, [authenticated]);

  const scan = useCallback(async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    if (mounted.current) setScanning(true);
    try {
      const nextStatus = await request('/api/monitors/status/');
      if (!mounted.current) return;
      setStatus(nextStatus);
      setLastUpdated(new Date());
      setRefreshWarning('');
    } catch (error) {
      if (mounted.current) setRefreshWarning(`Live refresh failed: ${error.message} Retrying automatically.`);
    } finally {
      requestInFlight.current = false;
      if (mounted.current) setScanning(false);
    }
  }, []);

  useEffect(() => {
    if (!authenticated) return undefined;
    scan();
    const timer = window.setInterval(scan, AUTO_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [authenticated, scan]);

  async function login(event) {
    event.preventDefault();
    try {
      await request('/api/site-access/login/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: accessPassword }),
      });
      setAccessPassword('');
      setAccessError('');
      setAuthenticated(true);
    } catch (error) {
      setAccessPassword('');
      setAccessError(error.message);
    }
  }

  async function logout() {
    try {
      await request('/api/site-access/logout/', { method: 'POST' });
    } finally {
      setAuthenticated(false);
      setStatus(null);
      setNotes({});
      setAccessPassword('');
      setAccessError('');
    }
  }

  async function copyExiva(name) {
    try {
      await navigator.clipboard.writeText(`Exiva "${name}"`);
      setCopiedName(name);
      window.setTimeout(() => { if (mounted.current) setCopiedName((current) => current === name ? '' : current); }, 1000);
    } catch (_) {
      // Clipboard permissions can be denied; live monitoring must continue unaffected.
    }
  }

  function openNote(enemy) {
    const existing = notes[enemy.name.toLocaleLowerCase()];
    setSelectedEnemy(enemy);
    setNoteDraft(existing?.observation || '');
    setNotePassword('');
    setEditingNote(false);
    setNoteMessage('');
    setNoteError('');
  }

  function closeNote() {
    setSelectedEnemy(null);
    setNotePassword('');
    setNoteError('');
  }

  async function saveNote(event) {
    event.preventDefault();
    const name = selectedEnemy.name;
    try {
      const saved = await request('/api/enemy-list/observations/', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character_name: name, observation: noteDraft, password: notePassword }),
      });
      setNotes((current) => {
        const next = { ...current };
        if (saved) next[name.toLocaleLowerCase()] = saved;
        else delete next[name.toLocaleLowerCase()];
        return next;
      });
      setEditingNote(false);
      setNoteMessage(saved ? 'Saved.' : 'Observation cleared.');
      setNoteError('');
    } catch (error) {
      setNoteError(error.message);
    } finally {
      setNotePassword('');
    }
  }

  if (accessLoading) return <main className="flex min-h-screen items-center justify-center bg-[#09090a] font-mono text-xs uppercase text-stone-600">Verifying access…</main>;

  if (!authenticated) return <main className="flex min-h-screen items-center justify-center bg-[#09090a] p-4 text-stone-100">
    <form onSubmit={login} className="w-full max-w-sm border border-stone-700 bg-[#101011] p-5 shadow-2xl">
      <p className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-red-400">Private access</p>
      <h1 className="mt-2 text-lg font-black uppercase tracking-wide">Tibia War Monitor</h1>
      <label htmlFor="site-password" className="mt-5 block text-[10px] font-bold uppercase tracking-widest text-stone-500">Password</label>
      <input id="site-password" type="password" required autoComplete="current-password" value={accessPassword} onChange={(event) => setAccessPassword(event.target.value)} className="mt-1 w-full border border-stone-700 bg-black px-3 py-2 text-sm outline-none focus:border-red-600" />
      {accessError && <p role="alert" className="mt-2 text-xs text-red-300">{accessError}</p>}
      <button type="submit" className="mt-4 border border-red-800 bg-red-950/60 px-4 py-2 text-xs font-black uppercase tracking-wide text-red-200 hover:bg-red-900">Enter</button>
    </form>
  </main>;

  return <main className="min-h-screen bg-[#09090a] text-stone-100">
    <div className="w-full px-2 py-2 sm:px-3">
      {refreshWarning && <div role="status" className="mt-2 border border-amber-900/70 bg-amber-950/30 px-3 py-1.5 text-xs text-amber-200">{refreshWarning}</div>}
      <MonitorSection type="enemy" guildName="Watch The Throne" world={status?.world || 'Monstera'} monitor={status?.monitors?.enemy} now={now} notes={notes} copiedName={copiedName} onCopy={copyExiva} onOpenNote={openNote} toolbar={<div className="ml-auto flex items-center gap-3 font-mono text-[10px] uppercase text-stone-500"><span>Auto 10s</span><span>Updated <span className="text-stone-300">{lastUpdated ? lastUpdated.toLocaleTimeString() : '—'}</span></span><button onClick={scan} disabled={scanning} className="h-7 border border-red-800 bg-red-950/60 px-3 font-sans text-[10px] font-black uppercase tracking-wide text-red-200 hover:bg-red-900 disabled:cursor-not-allowed disabled:border-stone-700 disabled:bg-stone-900 disabled:text-stone-600">{scanning ? 'Refreshing…' : 'Refresh'}</button><button onClick={logout} className="h-7 border border-stone-700 px-2 font-sans text-[9px] font-bold uppercase text-stone-500 hover:border-stone-500 hover:text-white">Logout</button></div>}/>
      <MonitorSection type="friend" guildName="Unfallen" world={status?.world || 'Monstera'} monitor={status?.monitors?.friend} now={now} notes={notes} copiedName={copiedName} onCopy={copyExiva} onOpenNote={openNote}/>

      {selectedEnemy && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeNote(); }}>
        <section role="dialog" aria-modal="true" aria-labelledby="observation-title" className="w-full max-w-md border border-stone-700 bg-[#111112] p-4 shadow-2xl">
          <div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-widest text-stone-500">Character</p><h2 id="observation-title" className="mt-1 text-sm font-bold text-white">{selectedEnemy.name}</h2></div><button type="button" onClick={closeNote} className="text-stone-500 hover:text-white" aria-label="Close observation">×</button></div>
          {!editingNote ? <div className="mt-4"><p className="text-[10px] font-bold uppercase tracking-widest text-stone-500">Observation</p><p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-stone-300">{notes[selectedEnemy.name.toLocaleLowerCase()]?.observation || 'No observation.'}</p><div className="mt-4 flex items-center gap-3"><button type="button" onClick={() => { setEditingNote(true); setNoteMessage(''); }} className="border border-stone-700 px-3 py-1.5 text-[10px] font-bold uppercase text-stone-300 hover:border-stone-500">Edit</button>{noteMessage && <span role="status" className="text-[10px] text-emerald-400">{noteMessage}</span>}</div></div> : <form onSubmit={saveNote} className="mt-4 space-y-3"><div><label htmlFor="note-password" className="text-[10px] font-bold uppercase tracking-widest text-stone-500">Password</label><input id="note-password" type="password" required autoComplete="off" value={notePassword} onChange={(event) => setNotePassword(event.target.value)} className="mt-1 w-full border border-stone-700 bg-black px-2 py-1.5 text-xs outline-none focus:border-red-600" /></div><div><label htmlFor="note-text" className="text-[10px] font-bold uppercase tracking-widest text-stone-500">Observation</label><textarea id="note-text" maxLength={2000} rows={4} value={noteDraft} onChange={(event) => setNoteDraft(event.target.value)} className="mt-1 w-full resize-y border border-stone-700 bg-black px-2 py-1.5 text-xs leading-5 outline-none focus:border-red-600" /></div>{noteError && <p role="alert" className="text-[10px] text-red-300">{noteError}</p>}<div className="flex gap-2"><button type="submit" className="border border-red-800 bg-red-950/50 px-3 py-1.5 text-[10px] font-bold uppercase text-red-200 hover:bg-red-900">Save</button><button type="button" onClick={() => { setEditingNote(false); setNotePassword(''); setNoteError(''); }} className="px-3 py-1.5 text-[10px] uppercase text-stone-500 hover:text-white">Cancel</button></div><p className="text-[9px] text-stone-600">Save an empty observation to delete it.</p></form>}
        </section>
      </div>}
    </div>
  </main>;
}
