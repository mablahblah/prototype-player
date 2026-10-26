// Vite config that builds a React site to live in a folder of the player,
// without editing any of the site's files.
//
// convert.py runs the site's own Vite with this config, passing SITE (the
// site's folder) and BASE (the address it is served from, e.g.
// /show/{name}/). The site's own vite.config is loaded and kept; on top of it:
//
// - Page addresses move into the hash (#/alt rather than /alt). A static
//   server only has a file for the site's front page, so an inner page's
//   address only survives a reload or a shared link when the server never
//   sees it.
// - Addresses written into the site's code that point at a file in its
//   public/ folder (/images/x.webp) get BASE in front, since those files no
//   longer sit at the root of the address.
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'

const SITE = process.env.SITE
const BASE = process.env.BASE
// Resolve packages from the site, since this file sits outside it.
const require = createRequire(path.join(SITE, 'package.json'))
const vite = await import(require.resolve('vite'))
const PUBLIC = path.join(SITE, 'public')
const ROUTER = '\0router-in-hash'
const ROUTER_PACKAGES = ['react-router-dom', 'react-router']

function routerModule(pkg) {
  const from = JSON.stringify(require.resolve(pkg))
  return `export * from ${from}
export { createHashRouter as createBrowserRouter, HashRouter as BrowserRouter } from ${from}`
}

function isPublicFile(rest) {
  const file = path.join(PUBLIC, rest)
  return file.startsWith(PUBLIC) && fs.existsSync(file) && fs.statSync(file).isFile()
}

const inFolder = {
  name: 'player-in-folder',
  enforce: 'pre',
  resolveId(id, importer) {
    // Only the site's own imports are swapped; the router module itself
    // still reaches the real package.
    if (ROUTER_PACKAGES.includes(id) && importer && !importer.startsWith('\0')
        && !importer.includes(`${path.sep}node_modules${path.sep}`)) {
      return `${ROUTER}:${id}`
    }
  },
  load(id) {
    if (id.startsWith(`${ROUTER}:`)) return routerModule(id.slice(ROUTER.length + 1))
  },
  // Run on the finished chunks, after JSON and the rest are already code.
  renderChunk(code) {
    let changed = false
    const out = code.replace(/(["'`])\/([^"'`\s?#]+)/g, (match, quote, rest) => {
      if (!isPublicFile(rest)) return match
      changed = true
      return quote + BASE + rest
    })
    return changed ? { code: out, map: null } : null
  },
}

const loaded = await vite.loadConfigFromFile(
  { command: 'build', mode: 'production' }, undefined, SITE)

export default vite.mergeConfig(loaded ? loaded.config : {}, {
  root: SITE,
  base: BASE,
  plugins: [inFolder],
  logLevel: 'warn',
  // One large script is expected for a prototype; the warning is noise.
  build: { chunkSizeWarningLimit: Infinity },
})
