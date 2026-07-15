import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Keep the repository limited to icons used by templates. All vendor SVGs are
// reproduced from lockfile-pinned npm packages instead of copied by hand.
const iconSets = [
  {
    packageName: "@fortawesome/fontawesome-free",
    sourceDir: "svgs/solid",
    targetDir: "assets/icons/fa/solid",
    icons: [
      "check",
      "circle-half-stroke",
      "earth-asia",
      "envelope",
      "house",
      "link",
      "location-dot",
      "magnifying-glass",
      "print",
      "rss",
      "triangle-exclamation",
    ],
  },
  {
    packageName: "@fortawesome/fontawesome-free",
    sourceDir: "svgs/regular",
    targetDir: "assets/icons/fa/regular",
    icons: ["moon", "sun"],
  },
  {
    packageName: "@fortawesome/fontawesome-free",
    sourceDir: "svgs/brands",
    targetDir: "assets/icons/fa/brands",
    icons: [
      "facebook",
      "github",
      "instagram",
      "linkedin",
      "twitter",
      "x-twitter",
      "youtube",
    ],
  },
  {
    packageName: "bootstrap-icons",
    sourceDir: "icons",
    targetDir: "assets/icons/bi",
    icons: [
      "archive",
      "arrow-up",
      "box-arrow-up-right",
      "file-earmark-richtext",
      "film",
      "info-circle",
      "rss",
    ],
  },
  {
    packageName: "lucide-static",
    sourceDir: "icons",
    targetDir: "assets/icons/lucide",
    icons: ["bot"],
  },
];

for (const iconSet of iconSets) {
  const packageRoot = dirname(
    fileURLToPath(import.meta.resolve(`${iconSet.packageName}/package.json`)),
  );
  const sourceRoot = join(packageRoot, iconSet.sourceDir);
  const targetRoot = join(process.cwd(), iconSet.targetDir);

  mkdirSync(targetRoot, { recursive: true });

  for (const icon of iconSet.icons) {
    copyFileSync(
      join(sourceRoot, `${icon}.svg`),
      join(targetRoot, `${icon}.svg`),
    );
  }
}
