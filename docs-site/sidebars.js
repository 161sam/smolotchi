/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    "index",
    {
      type: "category",
      label: "Getting Started",
      items: ["getting-started/installation", "getting-started/quickstart"],
    },
    {
      type: "category",
      label: "User Guide",
      items: ["user-guide/web-ui", "user-guide/stage-gates"],
    },
    {
      type: "category",
      label: "Architecture",
      items: ["architecture/overview", "architecture/pipelines"],
    },
    {
      type: "category",
      label: "Reference",
      items: [
        "reference/http-api",
        "reference/cli",
        "reference/configuration",
        "reference/actions",
        "reference/artifacts-and-reports",
      ],
    },
    {
      type: "category",
      label: "Deployment",
      items: ["deployment/systemd"],
    },
    {
      type: "category",
      label: "Developer Guide",
      items: ["dev/testing", "dev/docs-generation"],
    },
    {
      type: "category",
      label: "Troubleshooting",
      items: ["troubleshooting/common-issues"],
    },
    "glossary",
    {
      type: "category",
      label: "Meta",
      items: ["_meta/repo-map", "_meta/symbol-index", "_meta/code-index"],
    },
  ],
};

module.exports = sidebars;
