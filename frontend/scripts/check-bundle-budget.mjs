// #48 首屏构建体积预算门禁。
//
// 用法：npm run check:bundle [-- --dist <dir>] [-- --budget <file>]
// 解析 dist/index.html 实际引用的首屏资源，统计 raw 字节并与 bundle-budget.json
// 的预算比对，超限 exit 1（供 CI frontend-fast 在 build 后调用）。
//
// 统计口径（与预算文件 _meta.说明 一致）：
//   - <script type="module" src=...>   → 入口 JS（立即执行）
//   - <link rel="modulepreload" ...>   → 预取 JS（首屏传输的一部分；当前构建无此类，防未来回归）
//   - <link rel="stylesheet" ...>      → 首屏 CSS
// 判定用 raw 字节（确定性最高）；gzip 用 node:zlib 实时计算，仅展示不判定。
// 任何异常（dist 缺失、引用文件缺失、预算文件非法）一律 exit 1——门禁静默通过
// 等于没有门禁。

import { readFileSync, existsSync } from 'node:fs'
import { gzipSync } from 'node:zlib'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const FRONTEND_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')

function parseArgs(argv) {
  const args = { dist: join(FRONTEND_ROOT, 'dist'), budget: join(FRONTEND_ROOT, 'bundle-budget.json') }
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--dist') args.dist = resolve(argv[++i])
    else if (argv[i] === '--budget') args.budget = resolve(argv[++i])
    else if (argv[i] === '--help' || argv[i] === '-h') args.help = true
  }
  return args
}

function help() {
  console.log(`用法：node scripts/check-bundle-budget.mjs [--dist <dir>] [--budget <file>]

  --dist    构建产物目录（默认 frontend/dist）
  --budget  预算文件（默认 frontend/bundle-budget.json）

超限调整流程见 bundle-budget.json 的 _meta.超限调整流程。`)
}

const fmt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
const pad = (s, n) => (s.length >= n ? s : s + ' '.repeat(n - s.length))

function extractFirstScreenRefs(html) {
  const js = []
  const css = []
  for (const tag of html.match(/<script\b[^>]*>/g) ?? []) {
    const src = tag.match(/\bsrc="([^"]+)"/)?.[1]
    const type = tag.match(/\btype="([^"]*)"/)?.[1] ?? ''
    if (src && type === 'module') js.push(src)
  }
  for (const tag of html.match(/<link\b[^>]*>/g) ?? []) {
    const href = tag.match(/\bhref="([^"]+)"/)?.[1]
    const rel = tag.match(/\brel="([^"]+)"/)?.[1] ?? ''
    if (!href) continue
    if (rel === 'stylesheet') css.push(href)
    else if (rel === 'modulepreload') js.push(href)
  }
  return { js, css }
}

function measure(refs, distDir) {
  const measureOne = (ref, kind) => {
    if (/^https?:\/\//.test(ref)) return { ref, kind, error: '外链不计入本地产物' }
    const file = join(distDir, ref.replace(/^\/+/, ''))
    if (!existsSync(file)) return { ref, kind, error: '文件不存在（构建不完整？）' }
    const buf = readFileSync(file)
    return { ref, kind, raw: buf.length, gzip: gzipSync(buf).length }
  }
  const rows = [
    ...refs.js.map((r) => measureOne(r, 'JS')),
    ...refs.css.map((r) => measureOne(r, 'CSS')),
  ]
  const bad = rows.filter((r) => r.error)
  if (bad.length) throw new Error(bad.map((r) => `${r.kind} ${r.ref}: ${r.error}`).join('\n'))
  return rows
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  if (args.help) return help()

  const htmlPath = join(args.dist, 'index.html')
  if (!existsSync(htmlPath)) {
    console.error(`✗ 未找到 ${htmlPath}——请先 npm run build 再执行门禁`)
    process.exit(1)
  }
  const budget = JSON.parse(readFileSync(args.budget, 'utf8'))
  for (const key of ['entryJs', 'firstScreenCss']) {
    if (!Number.isFinite(budget[key]) || budget[key] <= 0) {
      console.error(`✗ 预算文件 ${args.budget} 缺少合法的 ${key}（正整数，单位字节）`)
      process.exit(1)
    }
  }

  const refs = extractFirstScreenRefs(readFileSync(htmlPath, 'utf8'))
  if (!refs.js.length && !refs.css.length) {
    console.error('✗ dist/index.html 未引用任何 module script / stylesheet——产物异常')
    process.exit(1)
  }
  const rows = measure(refs, args.dist)

  const sum = (kind) => rows.filter((r) => r.kind === kind).reduce((a, r) => a + r.raw, 0)
  const jsTotal = sum('JS')
  const cssTotal = sum('CSS')
  const checks = [
    { name: '入口 JS', raw: jsTotal, budget: budget.entryJs },
    { name: '首屏 CSS', raw: cssTotal, budget: budget.firstScreenCss },
  ]
  const failed = checks.filter((c) => c.raw > c.budget)

  console.log('首屏实载文件（dist/index.html 引用）:')
  for (const r of rows) {
    console.log(`  [${r.kind}] ${pad(r.ref, 48)} raw ${fmt(r.raw).padStart(9)} B   gzip ${fmt(r.gzip).padStart(9)} B`)
  }
  console.log('')
  for (const c of checks) {
    const ok = c.raw <= c.budget
    const margin = ok ? `余量 ${fmt(c.budget - c.raw)} B` : `超出 ${fmt(c.raw - c.budget)} B`
    console.log(`  ${ok ? '✓' : '✗'} ${c.name}: raw ${fmt(c.raw)} / 预算 ${fmt(c.budget)}（${margin}）`)
  }

  if (failed.length) {
    console.error('\n✗ 构建体积超预算：先按 bundle-budget.json 的 _meta.超限调整流程定位来源，勿直接抬预算')
    process.exit(1)
  }
  console.log('\n✓ 构建体积在预算内')
}

try {
  main()
} catch (err) {
  console.error(`✗ 体积门禁无法执行：${err.message}`)
  process.exit(1)
}
