import Link from "next/link";

const links = [
  ["Plan", "/"],
  ["Data", "/data/"],
  ["Capacity Lab", "/capacity-lab/"],
  ["Methods", "/methods/"],
] as const;

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="wordmark" href="/">
        GP Access Planner
      </Link>
      <nav aria-label="Primary navigation">
        {links.map(([label, href]) => (
          <Link href={href} key={href}>
            {label}
          </Link>
        ))}
      </nav>
      <span className="release-mark">JUN 2026 CUT</span>
    </header>
  );
}
