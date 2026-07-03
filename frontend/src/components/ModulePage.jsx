import React from 'react';

const modules = {
  leveling: {
    title: 'Leveling',
    status: 'Live',
    command: '/refresh',
    description: 'Tracks stored Tibia levels and reports gains during manual or scheduled refreshes.',
    actions: ['Review tracked characters', 'Run /refresh', 'Watch alert channel output'],
  },
  'death-alerts': {
    title: 'Death Alerts',
    status: 'Live',
    command: '/deaths Character Name',
    description: 'Stores character deaths and posts new death events after a baseline exists.',
    actions: ['Check recent deaths', 'Run /deaths', 'Confirm /setalerts channel'],
  },
  'guild-watch': {
    title: 'Guild Watch',
    status: 'Live',
    command: '/watchguild Guild Name',
    description: 'Keeps Tibia guild targets attached to a Discord server for guild operations.',
    actions: ['Add watched guild', 'Use /guild for lookup', 'Review watched targets'],
  },
  'world-online': {
    title: 'World Online',
    status: 'Live',
    command: '/online World',
    description: 'Shows current online players for a Tibia world and supports watched world targets.',
    actions: ['Scan world online list', 'Watch a world', 'Compare tracked worlds'],
  },
  leaderboards: {
    title: 'Leaderboards',
    status: 'Live',
    command: '/leaderboard',
    description: 'Ranks tracked characters by level and shows recent death memory.',
    actions: ['Open leaderboard', 'Add more characters', 'Refresh tracked data'],
  },
  roles: {
    title: 'Roles',
    status: 'Next',
    command: 'Planned',
    description: 'Future MEE6-style role automation from vocation, level range, guild, or world.',
    actions: ['Define role rules', 'Map vocation roles', 'Add sync command'],
  },
  teamspeak: {
    title: 'TeamSpeak',
    status: 'Next',
    command: 'Planned',
    description: 'Future x3tBot-style bridge for TeamSpeak identity and voice presence.',
    actions: ['Add TS credentials', 'Link TS identity', 'Show voice presence'],
  },
  settings: {
    title: 'Settings',
    status: 'Next',
    command: '/setalerts #channel',
    description: 'Server-level configuration for alerts, watched targets, and future automation options.',
    actions: ['Set alert channel', 'Review watched targets', 'Tune refresh behavior'],
  },
};

export function getModule(slug) {
  return modules[slug] ?? modules.settings;
}

export function moduleSlugs() {
  return Object.keys(modules);
}

export default function ModulePage({ slug }) {
  const module = getModule(slug);
  const isLive = module.status === 'Live';

  return (
    <div className="min-h-screen bg-[linear-gradient(120deg,#09090b_0%,#111827_48%,#18181b_100%)] px-4 py-6 text-stone-100 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="border border-stone-800 bg-zinc-950 p-5 shadow-[8px_8px_0_#1f2937]">
          <p className="font-mono text-xs uppercase text-lime-300">Module Control</p>
          <div className="mt-3 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="text-4xl font-black uppercase text-white sm:text-6xl">{module.title}</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-300">{module.description}</p>
            </div>
            <span className={isLive ? 'border border-lime-300 px-4 py-2 font-mono text-xs uppercase text-lime-300' : 'border border-stone-700 px-4 py-2 font-mono text-xs uppercase text-stone-400'}>
              {module.status}
            </span>
          </div>
        </header>

        <main className="mt-5 grid gap-5 lg:grid-cols-[1fr_22rem]">
          <section className="border border-stone-800 bg-zinc-950 p-5 shadow-[5px_5px_0_#292524]">
            <p className="font-mono text-xs uppercase text-amber-300">Primary Command</p>
            <div className="mt-3 border border-stone-800 bg-zinc-900 p-4 font-mono text-lg text-lime-200">
              {module.command}
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {module.actions.map((action) => (
                <div key={action} className="border border-stone-800 bg-zinc-900 p-4 text-sm text-stone-300">
                  {action}
                </div>
              ))}
            </div>
          </section>

          <aside className="grid gap-5">
            <section className="border border-stone-800 bg-zinc-950 p-5 shadow-[5px_5px_0_#292524]">
              <p className="font-mono text-xs uppercase text-cyan-300">MEE6-style Slot</p>
              <p className="mt-3 text-sm leading-6 text-stone-300">
                This page is where the module settings, toggles, logs, and configuration forms can live.
              </p>
            </section>
            <section className="border border-stone-800 bg-zinc-950 p-5 shadow-[5px_5px_0_#292524]">
              <p className="font-mono text-xs uppercase text-rose-300">x3tBot Angle</p>
              <p className="mt-3 text-sm leading-6 text-stone-300">
                Keep Tibia-specific operations visible: watched worlds, guild intelligence, deaths, levels, and voice
                coordination.
              </p>
            </section>
          </aside>
        </main>
      </div>
    </div>
  );
}
