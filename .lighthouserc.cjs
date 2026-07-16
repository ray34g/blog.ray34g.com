module.exports = {
  ci: {
    collect: {
      puppeteerScript: "./lhci.puppeteer.cjs",
      puppeteerLaunchOptions: {
        executablePath: "/usr/bin/google-chrome",
        userDataDir: "/tmp/lhci-blog-profile",
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
      },
      startServerCommand: "python3 -u -m http.server 1313 --bind 127.0.0.1 --directory public",
      startServerReadyPattern: "Serving HTTP on 127.0.0.1 port 1313",
      url: ["http://localhost:1313/"],
      numberOfRuns: 3,
      settings: {
        onlyCategories: ["performance", "seo", "accessibility", "best-practices"],
      },
    },
    assert: {
      assertions: {
        "categories:performance": ["warn", { minScore: 0.9 }],
        "categories:accessibility": ["warn", { minScore: 0.9 }],
        "categories:best-practices": ["warn", { minScore: 0.9 }],
        "categories:seo": ["warn", { minScore: 0.9 }],
      },
    },
  },
};
