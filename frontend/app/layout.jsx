import Link from 'next/link';
import Image from 'next/image';
import '../src/input.css';

export const metadata = {
  title: 'YalaharBot',
  description: 'Dashboard for managing Tibia characters and Discord bot features.',
  icons: {
    icon: '/favicon.ico',
    apple: '/logo192.png',
  },
  manifest: '/manifest.json',
};

export default function RootLayout({ children }) {
  const navItems = [
    { href: '/', label: 'Dashboard', tag: 'Live' },
    { href: '/characters', label: 'Characters', tag: 'Core' },
  ];
  const modules = [
    { label: 'Leveling', slug: 'leveling', state: 'on' },
    { label: 'Death Alerts', slug: 'death-alerts', state: 'on' },
    { label: 'Guild Watch', slug: 'guild-watch', state: 'on' },
    { label: 'World Online', slug: 'world-online', state: 'on' },
    { label: 'Leaderboards', slug: 'leaderboards', state: 'on' },
    { label: 'Roles', slug: 'roles', state: 'next' },
    { label: 'TeamSpeak', slug: 'teamspeak', state: 'next' },
    { label: 'Settings', slug: 'settings', state: 'next' },
  ];

  return (
    <html lang="en">
      <body className="bg-zinc-950">
        <div className="min-h-screen bg-zinc-950 text-stone-100 lg:grid lg:grid-cols-[17rem_1fr]">
          <aside className="border-b border-stone-800 bg-[#08080a] lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
            <div className="flex items-center justify-between gap-3 border-b border-stone-800 px-4 py-4 lg:block">
              <div className="flex items-center gap-3 lg:block">
                <Image
                  src="/logoYalaharbot.png"
                  alt="YalaharBot logo"
                  width={56}
                  height={56}
                  priority
                  className="h-12 w-12 border border-stone-800 bg-zinc-900 object-contain p-1 lg:h-16 lg:w-16"
                />
                <div className="lg:mt-3">
                  <p className="font-mono text-[10px] font-black uppercase text-lime-300">Control Panel</p>
                  <h1 className="mt-1 text-xl font-black uppercase text-white">YalaharBot</h1>
                </div>
              </div>
              <div className="border border-lime-300 px-2 py-1 font-mono text-[10px] uppercase text-lime-300 lg:mt-4 lg:inline-block">
                Online
              </div>
            </div>

            <nav className="px-3 py-3">
              <p className="px-2 font-mono text-[10px] font-black uppercase text-stone-500">Pages</p>
              <div className="mt-2 grid gap-2">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex min-h-12 items-center justify-between border border-stone-700 bg-zinc-900 px-3 py-3 text-sm font-black uppercase text-stone-100 shadow-[3px_3px_0_#1f2937] hover:border-lime-300 hover:bg-lime-300 hover:text-zinc-950 active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                  >
                    <span>{item.label}</span>
                    <span className="border border-current px-2 py-1 font-mono text-[10px]">{item.tag}</span>
                  </Link>
                ))}
              </div>
            </nav>

            <section className="hidden px-3 pb-4 lg:block">
              <p className="px-2 font-mono text-[10px] font-black uppercase text-stone-500">Bot Modules</p>
              <div className="mt-2 grid gap-2">
                {modules.map((module) => (
                  <Link
                    key={module.slug}
                    href={`/modules/${module.slug}`}
                    className="flex min-h-10 w-full items-center justify-between border border-stone-800 bg-zinc-900 px-3 py-2 text-left text-xs font-bold text-stone-200 shadow-[2px_2px_0_#1f2937] hover:border-lime-300 hover:bg-zinc-800 hover:text-lime-300 active:translate-x-[1px] active:translate-y-[1px] active:shadow-none"
                  >
                    <span>{module.label}</span>
                    <span className={module.state === 'on' ? 'rounded-none border border-lime-300 px-2 py-1 font-mono text-[10px] uppercase text-lime-300' : 'rounded-none border border-stone-700 px-2 py-1 font-mono text-[10px] uppercase text-stone-500'}>
                      {module.state}
                    </span>
                  </Link>
                ))}
              </div>
            </section>

            <section className="hidden px-3 pb-5 lg:block">
              <div className="border border-stone-800 bg-zinc-950 p-3">
                <p className="font-mono text-[10px] uppercase text-amber-300">Quick Setup</p>
                <p className="mt-2 text-xs leading-5 text-stone-400">
                  Use /setalerts, /watchworld, and /watchguild to turn this server into a live Tibia console.
                </p>
              </div>
            </section>
          </aside>

          <main className="min-w-0">{children}</main>
        </div>
      </body>
    </html>
  );
}
