export const VOCATION_GROUPS = [
  { key: 'knights', label: 'Knights', accent: 'border-amber-700/70', level: 'text-amber-300' },
  { key: 'paladins', label: 'Paladins', accent: 'border-lime-700/70', level: 'text-lime-300' },
  { key: 'sorcerers', label: 'Sorcerers', accent: 'border-violet-700/70', level: 'text-violet-300' },
  { key: 'druids', label: 'Druids', accent: 'border-emerald-700/70', level: 'text-emerald-300' },
  { key: 'monks', label: 'Monks', accent: 'border-cyan-700/70', level: 'text-cyan-300' },
  { key: 'other', label: 'Other / Unknown', accent: 'border-stone-700', level: 'text-stone-300' },
];

export function vocationGroup(vocation = '') {
  const normalized = String(vocation).toLocaleLowerCase();
  if (normalized.includes('knight')) return 'knights';
  if (normalized.includes('paladin')) return 'paladins';
  if (normalized.includes('sorcerer')) return 'sorcerers';
  if (normalized.includes('druid')) return 'druids';
  if (normalized.includes('monk')) return 'monks';
  return 'other';
}

export function groupEnemies(enemies = []) {
  const grouped = Object.fromEntries(VOCATION_GROUPS.map(({ key }) => [key, []]));
  enemies.forEach((enemy) => grouped[vocationGroup(enemy.vocation)].push(enemy));
  Object.values(grouped).forEach((players) => players.sort(
    (left, right) => Number(right.level) - Number(left.level) || left.name.localeCompare(right.name)
  ));
  return grouped;
}
