import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import YAML from "yaml";

const rootDir = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const policy = YAML.parse(await readFile(path.join(rootDir, "config", "theme-backport-policy.yaml"), "utf8"));
const manifest = JSON.parse(await readFile(path.join(rootDir, "theme-backport.lock.json"), "utf8"));
const packageJson = JSON.parse(await readFile(path.join(rootDir, "package.json"), "utf8"));

assertEqual(manifest.schemaVersion, policy.schemaVersion, "schema version");
assertEqual(manifest.contractVersion, String(policy.contractVersion), "contract version");
assertEqual(manifest.sourceRepository, policy.sourceRepository, "source repository");
assertEqual(manifest.bootstrapVersion, String(policy.bootstrapVersion), "manifest Bootstrap version");
assertEqual(packageJson.devDependencies?.bootstrap, String(policy.bootstrapVersion), "package Bootstrap version");
if (!/^[0-9a-f]{40}$/.test(manifest.sourceCommit || "")) {
  throw new Error("theme sourceCommit must be a full Git SHA");
}

const expected = [...policy.allowedFiles].sort();
const actual = manifest.files.map((entry) => entry.path).sort();
assertEqual(JSON.stringify(actual), JSON.stringify(expected), "allowlisted file set");

for (const entry of manifest.files) {
  if (path.isAbsolute(entry.path) || entry.path.includes("..") || entry.path.includes("\\")) {
    throw new Error(`unsafe theme path: ${entry.path}`);
  }
  const content = await readFile(path.join(rootDir, entry.path));
  assertEqual(sha256(content), entry.sha256, `${entry.path} SHA-256`);
  rejectPrivateMaterial(entry.path, content.toString("utf8"));
}

console.log(
  `[theme-backport] verified ${manifest.contractVersion} from ${manifest.sourceCommit.slice(0, 12)}`,
);

function assertEqual(actualValue, expectedValue, label) {
  if (actualValue !== expectedValue) {
    throw new Error(`${label} mismatch: expected ${expectedValue}, received ${actualValue}`);
  }
}

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

function rejectPrivateMaterial(relativePath, text) {
  const forbidden = [/\/workspaces\//, /BLOG_ARTIFACT_DEPLOY_KEY/, /PORTAL_ARTIFACT_DEPLOY_KEY/, /BEGIN [A-Z ]*PRIVATE KEY/];
  for (const pattern of forbidden) {
    if (pattern.test(text)) throw new Error(`private material matched ${pattern} in ${relativePath}`);
  }
}
