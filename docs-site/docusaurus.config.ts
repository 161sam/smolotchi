import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";

const config: Config = {
  title: "Smolotchi Docs",
  tagline: "Code-accurate wiki documentation",
  url: "https://161sam.github.io",
  baseUrl: "/smolotchi/",
  favicon: "img/favicon.ico",
  organizationName: "161sam",
  projectName: "smolotchi",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "throw",
  markdown: {
    mermaid: true,
  },
  themes: ["@docusaurus/theme-mermaid"],
  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.js",
          editUrl: "https://github.com/161sam/smolotchi/tree/main/docs-site/",
          routeBasePath: "/",
          exclude: ["**/*.test.{js,ts,jsx,tsx}", "**/__tests__/**"],
        },
        theme: {
          customCss: "./src/css/custom.css",
        },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: "Smolotchi",
      items: [
        { type: "doc", docId: "getting-started/installation", label: "Docs" },
        {
          href: "https://github.com/161sam/smolotchi",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [
            {
              label: "Getting Started",
              to: "/getting-started/installation",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Smolotchi`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    mermaid: {
      options: {
        securityLevel: "strict",
      },
    },
  },
};

export default config;
