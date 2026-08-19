import "@fontsource-variable/source-sans-3";
import "@fontsource/ibm-plex-mono/400.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "GP Access Planner", template: "%s · GP Access Planner" },
  description:
    "Public-data planning for recorded general-practice access pressure in England.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <SiteHeader />
        {children}
        <footer className="site-footer">
          <p>GP Access Planner · Public sources · Non-commercial use</p>
          <p>
            Contains information from NHS England, licensed under the current source
            terms. No NHS endorsement is implied.
          </p>
        </footer>
      </body>
    </html>
  );
}
