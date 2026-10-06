'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Image from 'next/image';
import { apiFetch } from '../api';

const endpoints = {
  characters: '/api/characters/',
  deaths: '/api/character-deaths/',
  settings: '/api/server-settings/',
  watchedGuilds: '/api/watched-guilds/',
  watchedWorlds: '/api/watched-worlds/',
};

const commandGroups = [
  { title: 'Identity', commands: ['/add', '/mychars', '/whois', '/lookup'] },
  { title: 'Tracking', commands: ['/refresh', '/deaths', '/leaderboard'] },
  { title: 'Server Ops', commands: ['/setalerts', '/watchworld', '/watchguild', '/watched'] },
  { title: 'Intel', commands: ['/online', '/guild'] },
];

const modules = [
  { name: 'Level Alerts', status: 'live', accent: 'bg-lime-300', detail: 'Posts gains after tracked refreshes.' },
  { name: 'Death Feed', status: 'live', accent: 'bg-rose-300', detail: 'Detects remembered deaths from Tibia.com.' },
  { name: 'World Scanner', status: 'ready', accent: 'bg-cyan-300', detail: 'Looks up online lists by world.' },
  { name: 'Guild Watch', status: 'ready', accent: 'bg-amber-300', detail: 'Stores watched guild targets per server.' },
  { name: 'Role Sync', status: 'next', accent: 'bg-stone-500', detail: 'MEE6-style roles by vocation and level.' },
  { name: 'TeamSpeak Bridge', status: 'next', accent: 'bg-stone-500', detail: 'x3tBot-style voice identity layer.' },
];

async function fetchJson(url) {
  const response = await apiFetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

function apiRows(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.results ?? [];
}

function Frame({ title, kicker, action, children }) {
  return (
    <section className="border border-stone-800 bg-zinc-950/95 p-4 shadow-[5px_5px_0_#292524]">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          {kicker && <p className="font-mono text-[11px] uppercase text-lime-300">{kicker}</p>}
          <h2 className="text-base font-black uppercase text-white">{title}</h2>
        </div>
        {action && <div>{action}</div>}
      </div>
      {children}
    </section>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className={`border border-stone-800 p-4 text-zinc-950 ${tone}`}>
      <div className="font-mono text-3xl font-black">{value}</div>
      <div className="text-xs font-black uppercase">{label}</div>
    </div>
  );
}

function Empty({ children }) {
  return <p className="border border-dashed border-stone-700 p-4 text-sm text-stone-400">{children}</p>;
}

function Home() {
  const [data, setData] = useState({
    characters: [],
    deaths: [],
    settings: [],
    watchedGuilds: [],
    watchedWorlds: [],
  });
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [characters, deaths, settings, watchedGuilds, watchedWorlds] = await Promise.all([
          fetchJson(endpoints.characters),
          fetchJson(endpoints.deaths),
          fetchJson(endpoints.settings),
          fetchJson(endpoints.watchedGuilds),
          fetchJson(endpoints.watchedWorlds),
        ]);

        setData({
          characters: apiRows(characters),
          deaths: apiRows(deaths),
          settings: apiRows(settings),
          watchedGuilds: apiRows(watchedGuilds),
          watchedWorlds: apiRows(watchedWorlds),
        });
        setError('');
      } catch (err) {
        setError(err.message);
      }
    }

    loadDashboard();
  }, []);

  const topCharacters = useMemo(
    () => [...data.characters].sort((a, b) => b.level - a.level || a.name.localeCompare(b.name)).slice(0, 8),
    [data.characters]
  );
  const recentDeaths = useMemo(() => data.deaths.slice(0, 6), [data.deaths]);
  const worlds = useMemo(() => {
    return [...new Set(data.characters.map((character) => character.world).filter(Boolean))].sort();
  }, [data.characters]);
  const vocationCounts = useMemo(() => {
    return data.characters.reduce((counts, character) => {
      counts[character.vocation] = (counts[character.vocation] || 0) + 1;
      return counts;
    }, {});
  }, [data.characters]);

  return (
    <div className="min-h-screen bg-[linear-gradient(120deg,#09090b_0%,#111827_45%,#1c1917_100%)] text-stone-100">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="grid gap-5 border border-stone-800 bg-zinc-950/95 p-5 shadow-[8px_8px_0_#365314] lg:grid-cols-[1.1fr_0.9fr]">
          <div className="grid min-w-0 gap-4 sm:grid-cols-[auto_1fr] sm:items-center">
            <Image
              src="/logoYalaharbot.png"
              alt="YalaharBot logo"
              width={112}
              height={112}
              priority
              className="h-24 w-24 border border-stone-800 bg-zinc-900 object-contain p-2 shadow-[5px_5px_0_#1f2937]"
            />
            <div className="min-w-0">
              <p className="font-mono text-xs uppercase text-lime-300">MEE6 controls + x3tBot guild ops</p>
              <h1 className="mt-2 break-words text-4xl font-black uppercase leading-tight text-white sm:text-6xl">YalaharBot</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-300">
                Discord automation for Tibia servers: character identity, alert feeds, tracked worlds, guild intel,
                and a roster console built for repeat daily use.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-2">
            <Stat label="Tracked" value={data.characters.length} tone="bg-lime-300" />
            <Stat label="Deaths" value={data.deaths.length} tone="bg-rose-300" />
            <Stat label="Servers" value={data.settings.length} tone="bg-cyan-300" />
            <Stat label="Worlds" value={data.watchedWorlds.length || worlds.length} tone="bg-amber-300" />
          </div>
        </header>

        {error && <div className="mt-5 border border-red-400 bg-red-950 p-4 text-sm text-red-100">{error}</div>}

        <main className="mt-5 grid gap-5 xl:grid-cols-12">
          <div className="grid gap-5 xl:col-span-8">
            <Frame title="Automation Modules" kicker="bot feature board">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {modules.map((module) => (
                  <div key={module.name} className="border border-stone-800 bg-zinc-900 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className={`h-3 w-3 ${module.accent}`} />
                      <span className="font-mono text-[10px] uppercase text-stone-400">{module.status}</span>
                    </div>
                    <h3 className="mt-3 font-black uppercase text-white">{module.name}</h3>
                    <p className="mt-2 text-xs leading-5 text-stone-400">{module.detail}</p>
                  </div>
                ))}
              </div>
            </Frame>

            <div className="grid gap-5 lg:grid-cols-2">
              <Frame title="Tracked Leaderboard" kicker="highest levels">
                {topCharacters.length ? (
                  <div className="grid gap-2">
                    {topCharacters.map((character, index) => (
                      <div
                        key={character.id}
                        className="grid grid-cols-[2rem_1fr_auto] items-center gap-3 border border-stone-800 bg-zinc-900 p-3"
                      >
                        <span className="font-mono text-xs text-lime-300">{index + 1}</span>
                        <div>
                          <div className="font-bold text-white">{character.name}</div>
                          <div className="text-xs text-stone-400">
                            {character.vocation} - {character.world}
                          </div>
                        </div>
                        <span className="font-mono text-lg font-black text-white">{character.level}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty>Use /add in Discord to start building the leaderboard.</Empty>
                )}
              </Frame>

              <Frame title="Recent Death Feed" kicker="alert memory">
                {recentDeaths.length ? (
                  <div className="grid gap-2">
                    {recentDeaths.map((death) => (
                      <div key={death.id} className="border border-stone-800 bg-zinc-900 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <span className="font-bold text-white">Character #{death.character}</span>
                          <span className="font-mono text-xs text-rose-300">LV {death.level}</span>
                        </div>
                        <p className="mt-1 text-xs text-stone-300">{death.killers}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty>No remembered deaths yet. Run /deaths or /refresh after tracking characters.</Empty>
                )}
              </Frame>
            </div>

            <Frame title="Command Matrix" kicker="Discord slash surface">
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                {commandGroups.map((group) => (
                  <div key={group.title} className="border border-stone-800 bg-zinc-900 p-3">
                    <h3 className="text-xs font-black uppercase text-amber-300">{group.title}</h3>
                    <div className="mt-3 grid gap-2 font-mono text-xs text-lime-200">
                      {group.commands.map((command) => (
                        <span key={command}>{command}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Frame>
          </div>

          <aside className="grid gap-5 xl:col-span-4">
            <Frame title="Server Alert Routes" kicker="configured with /setalerts">
              {data.settings.length ? (
                <div className="grid gap-2">
                  {data.settings.map((setting) => (
                    <div key={setting.id} className="border border-stone-800 bg-zinc-900 p-3 font-mono text-xs">
                      <div className="text-cyan-300">guild {setting.guild_id}</div>
                      <div className="mt-1 text-stone-300">channel {setting.alert_channel_id}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <Empty>No alert route configured. Use /setalerts #channel.</Empty>
              )}
            </Frame>

            <Frame title="Watched Targets" kicker="worlds and guilds">
              <div className="grid gap-4">
                <div>
                  <h3 className="text-xs font-black uppercase text-cyan-300">Worlds</h3>
                  <p className="mt-2 text-sm text-stone-300">
                    {data.watchedWorlds.map((world) => world.name).join(', ') || worlds.join(', ') || 'None'}
                  </p>
                </div>
                <div>
                  <h3 className="text-xs font-black uppercase text-amber-300">Guilds</h3>
                  <p className="mt-2 text-sm text-stone-300">
                    {data.watchedGuilds.map((guild) => guild.name).join(', ') || 'None'}
                  </p>
                </div>
              </div>
            </Frame>

            <Frame title="Vocation Mix" kicker="tracked roster">
              {Object.keys(vocationCounts).length ? (
                <div className="grid gap-2">
                  {Object.entries(vocationCounts).map(([vocation, count]) => (
                    <div key={vocation} className="flex items-center justify-between border-b border-stone-800 pb-2">
                      <span className="text-sm text-stone-300">{vocation}</span>
                      <span className="font-mono text-lime-300">{count}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <Empty>No vocation data yet.</Empty>
              )}
            </Frame>

            <Frame title="Ops Pipeline" kicker="x3tBot rhythm">
              <div className="grid gap-3 text-sm">
                <div className="border-l-4 border-lime-300 bg-zinc-900 p-3">
                  Track characters with /add or /lookup.
                </div>
                <div className="border-l-4 border-cyan-300 bg-zinc-900 p-3">
                  Configure alert output with /setalerts.
                </div>
                <div className="border-l-4 border-rose-300 bg-zinc-900 p-3">
                  Let the 15 minute loop post deaths and level gains.
                </div>
              </div>
            </Frame>
          </aside>
        </main>
      </div>
    </div>
  );
}

export default Home;
