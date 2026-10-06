'use client';

import React, { useMemo, useState } from 'react';
import axios from 'axios';
import { apiUrl } from '../api';

const botModules = [
  { label: 'Death Alerts', state: 'armed', detail: 'Posts tracked character deaths to the alert channel.' },
  { label: 'Level Watch', state: 'armed', detail: 'Reports level gains during the refresh cycle.' },
  { label: 'Guild Intel', state: 'ready', detail: 'Use /guild and /watchguild to inspect guild targets.' },
  { label: 'World Online', state: 'ready', detail: 'Use /online and /watchworld for world visibility.' },
  { label: 'Role Sync', state: 'planned', detail: 'Future MEE6-style roles from level, vocation, and guild.' },
  { label: 'TS Bridge', state: 'planned', detail: 'Future x3tBot-style voice identity bridge.' },
];

const commandPresets = [
  '/add Character Name',
  '/mychars',
  '/whois @user',
  '/deaths Character Name',
  '/refresh',
  '/leaderboard',
  '/setalerts #channel',
  '/online World',
];

function statusClass(state) {
  if (state === 'armed') return 'border-emerald-400 bg-emerald-400 text-zinc-950';
  if (state === 'ready') return 'border-cyan-300 bg-cyan-300 text-zinc-950';
  return 'border-stone-700 bg-zinc-900 text-stone-300';
}

function ShellPanel({ title, eyebrow, children }) {
  return (
    <section className="border border-stone-800 bg-zinc-950 p-4 shadow-[5px_5px_0_#27272a]">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          {eyebrow && <p className="font-mono text-xs uppercase text-amber-300">{eyebrow}</p>}
          <h2 className="text-lg font-black uppercase text-white">{title}</h2>
        </div>
        <div className="h-3 w-3 bg-lime-300 shadow-[0_0_16px_#bef264]" />
      </div>
      {children}
    </section>
  );
}

const TibiaCharacter = () => {
  const [characterName, setCharacterName] = useState('');
  const [characterData, setCharacterData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const otherCharacters = useMemo(() => characterData?.other_characters ?? [], [characterData]);

  const fetchCharacterData = async () => {
    if (!characterName.trim()) {
      setError('Enter a character name first.');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(
        apiUrl(`/api/characters/fetch_tibia_data/?name=${encodeURIComponent(characterName.trim())}`),
        { withCredentials: true },
      );
      setCharacterData(response.data);
      setError('');
    } catch (err) {
      setCharacterData(null);
      setError('Character lookup failed. Check the spelling and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#1f2937,transparent_34%),linear-gradient(135deg,#09090b_0%,#18181b_50%,#111827_100%)] px-4 py-6 text-stone-100 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-12">
        <header className="border border-stone-800 bg-zinc-950/90 p-5 shadow-[8px_8px_0_#334155] lg:col-span-12">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="font-mono text-xs uppercase text-lime-300">Character command center</p>
              <h1 className="mt-2 text-3xl font-black uppercase text-white sm:text-5xl">Roster Control</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-300">
                A Discord-bot console for Tibia identity lookup, account rosters, alert readiness, and guild operations.
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="border border-stone-700 bg-stone-900 p-3">
                <div className="font-mono text-xl font-black text-lime-300">15m</div>
                <div className="text-xs uppercase text-stone-400">Alert Loop</div>
              </div>
              <div className="border border-stone-700 bg-stone-900 p-3">
                <div className="font-mono text-xl font-black text-cyan-300">16</div>
                <div className="text-xs uppercase text-stone-400">Cmds</div>
              </div>
              <div className="border border-stone-700 bg-stone-900 p-3">
                <div className="font-mono text-xl font-black text-rose-300">2</div>
                <div className="text-xs uppercase text-stone-400">Alert Types</div>
              </div>
            </div>
          </div>
        </header>

        <div className="grid gap-5 lg:col-span-7">
          <ShellPanel title="Tibia Lookup" eyebrow="NabBot core">
            <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
              <input
                type="text"
                value={characterName}
                onChange={(event) => setCharacterName(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') fetchCharacterData();
                }}
                placeholder="Enter character name"
                className="border border-stone-700 bg-zinc-900 px-4 py-3 text-sm text-white outline-none ring-lime-300 placeholder:text-stone-500 focus:ring-2"
              />
              <button
                onClick={fetchCharacterData}
                className="border border-lime-300 bg-lime-300 px-5 py-3 text-sm font-black uppercase text-zinc-950 hover:bg-zinc-950 hover:text-lime-300"
              >
                {loading ? 'Scanning' : 'Scan'}
              </button>
            </div>
            {error && <p className="mt-3 border border-rose-400 bg-rose-950 p-3 text-sm text-rose-100">{error}</p>}
          </ShellPanel>

          <ShellPanel title="Identity Card" eyebrow="Discord link preview">
            {characterData ? (
              <div className="grid gap-4 sm:grid-cols-[1fr_auto]">
                <div>
                  <h3 className="text-3xl font-black uppercase text-white">{characterData.name}</h3>
                  <p className="mt-2 text-sm text-stone-300">
                    Level {characterData.level} {characterData.vocation} on {characterData.world}
                  </p>
                  <p className="mt-2 font-mono text-xs text-stone-500">
                    Last login: {characterData.last_login || 'Unknown'}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="border border-stone-800 bg-zinc-900 p-4">
                    <div className="font-mono text-3xl font-black text-lime-300">{characterData.level}</div>
                    <div className="text-xs uppercase text-stone-500">Level</div>
                  </div>
                  <div className="border border-stone-800 bg-zinc-900 p-4">
                    <div className="font-mono text-3xl font-black text-cyan-300">{otherCharacters.length}</div>
                    <div className="text-xs uppercase text-stone-500">Alts</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="border border-dashed border-stone-700 p-6 text-sm text-stone-400">
                Search a character to build the Discord identity card used by /lookup, /add, /whois, and /mychars.
              </div>
            )}
          </ShellPanel>

          <ShellPanel title="Account Roster" eyebrow="x3tBot-style scan">
            {otherCharacters.length ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {otherCharacters.map((charName) => (
                  <div key={charName} className="border border-stone-800 bg-zinc-900 p-3 font-bold text-stone-100">
                    {charName}
                  </div>
                ))}
              </div>
            ) : (
              <div className="border border-dashed border-stone-700 p-4 text-sm text-stone-400">
                Other characters from the same Tibia account will appear here.
              </div>
            )}
          </ShellPanel>
        </div>

        <aside className="grid gap-5 lg:col-span-5">
          <ShellPanel title="Automation Modules" eyebrow="MEE6-style toggles">
            <div className="grid gap-2">
              {botModules.map((module) => (
                <div key={module.label} className="grid grid-cols-[auto_1fr] gap-3 border border-stone-800 bg-zinc-900 p-3">
                  <span className={`self-start border px-2 py-1 font-mono text-[10px] uppercase ${statusClass(module.state)}`}>
                    {module.state}
                  </span>
                  <div>
                    <h3 className="font-bold text-white">{module.label}</h3>
                    <p className="mt-1 text-xs leading-5 text-stone-400">{module.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </ShellPanel>

          <ShellPanel title="Command Presets" eyebrow="Copy into Discord">
            <div className="grid gap-2 font-mono text-xs">
              {commandPresets.map((command) => (
                <div key={command} className="border border-stone-800 bg-zinc-900 p-3 text-lime-200">
                  {command}
                </div>
              ))}
            </div>
          </ShellPanel>

          <ShellPanel title="Alert Pipeline" eyebrow="live behavior">
            <div className="space-y-3 text-sm text-stone-300">
              <div className="flex items-center justify-between border-b border-stone-800 pb-2">
                <span>Manual refresh</span>
                <span className="font-mono text-lime-300">/refresh</span>
              </div>
              <div className="flex items-center justify-between border-b border-stone-800 pb-2">
                <span>Scheduled cycle</span>
                <span className="font-mono text-cyan-300">15 min</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Output channel</span>
                <span className="font-mono text-amber-300">/setalerts</span>
              </div>
            </div>
          </ShellPanel>
        </aside>
      </div>
    </div>
  );
};

export default TibiaCharacter;
