import ModulePage, { getModule, moduleSlugs } from '../../../src/components/ModulePage';

export const dynamicParams = false;

export function generateStaticParams() {
  return moduleSlugs().map((module) => ({ module }));
}

export async function generateMetadata({ params }) {
  const resolvedParams = await params;
  const module = getModule(resolvedParams.module);
  return {
    title: `${module.title} - YalaharBot`,
  };
}

export default async function BotModulePage({ params }) {
  const resolvedParams = await params;
  return <ModulePage slug={resolvedParams.module} />;
}
