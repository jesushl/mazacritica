import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const here = dirname(fileURLToPath(import.meta.url))
const src = resolve(here, '..')
const sheets = [
  'App.css',
  'index.css',
  'components/AppShell.css',
  'components/Feed.css',
  'components/NoteDetail.css',
  'components/CommentThread.css',
  'components/AuthDialog.css',
  'components/JudicialPage.css',
]
const appCss = sheets
  .filter((name) => name !== 'index.css')
  .map((name) => readFileSync(resolve(src, name), 'utf8'))
  .join('\n')
const indexCss = readFileSync(resolve(src, 'index.css'), 'utf8')

function mediaBlock(css, width) {
  const marker = `@media (max-width: ${width}px)`
  const start = css.indexOf(marker)
  expect(start, marker).toBeGreaterThan(-1)
  const open = css.indexOf('{', start)
  let depth = 0
  for (let index = open; index < css.length; index += 1) {
    if (css[index] === '{') depth += 1
    if (css[index] === '}') {
      depth -= 1
      if (depth === 0) return css.slice(start, index + 1)
    }
  }
  throw new Error(`Bloque ${marker} sin cerrar`)
}

function hides(block, selector) {
  const pattern = new RegExp(`${selector.replace('.', '\\.')}\\s*\\{[^}]*display:\\s*none`)
  return pattern.test(block)
}

describe('contrato responsive', () => {
  const narrow = mediaBlock(appCss, 760)
  const tablet = mediaBlock(appCss, 1120)

  it('keeps navigation, login and the editorial rail reachable', () => {
    expect(hides(narrow, '.sidebar')).toBe(false)
    expect(hides(narrow, '.login-button')).toBe(false)
    expect(hides(narrow, '.right-rail')).toBe(false)
    expect(hides(tablet, '.right-rail')).toBe(false)
    expect(hides(narrow, '.note-source')).toBe(false)
    expect(hides(narrow, '.note-tag')).toBe(false)
    expect(hides(tablet, '.note-source')).toBe(false)
    expect(narrow).toMatch(/grid-template-columns:\s*minmax\(0,\s*1fr\)/)
    expect(tablet).toMatch(/grid-area:\s*rail/)
  })

  it('uses 44px targets and readable chip text without the Vite root padding', () => {
    expect(appCss).not.toMatch(/#root\s*\{[^}]*max-width:\s*1280px/)
    expect(appCss).not.toMatch(/#root\s*\{[^}]*padding:\s*2rem/)
    expect(appCss).toMatch(/\.filter-chip[\s\S]*font-size:\s*12px/)
    expect(appCss).toMatch(/\.note-tag[\s\S]*font-size:\s*12px/)
    for (const selector of [
      '.filter-chip',
      '.note-actions button',
      '.variant-tab',
      '.comment-actions button',
      '.search-box',
      '.auth-dialog button',
      '.postal-search button',
      '.comment-composer button',
      '.note-composer button',
    ]) {
      expect(appCss, selector).toMatch(
        new RegExp(`${selector.replace('.', '\\.')}[\\s\\S]{0,220}min-height:\\s*44px`),
      )
    }
  })

  it('keeps a visible focus style and hides the collapsed header from the tab order', () => {
    const styles = `${indexCss}\n${appCss}`
    expect(appCss).not.toMatch(/\.search-box input\s*\{[^}]*outline:\s*0/)
    expect(styles).toMatch(/button:focus-visible/)
    expect(styles).toMatch(/a:focus-visible/)
    expect(styles).toMatch(/input:focus-visible/)
    expect(styles).toMatch(/textarea:focus-visible/)
    expect(styles).toMatch(/summary:focus-visible/)
    expect(appCss).toMatch(/\.search-box input:focus-visible/)
    expect(appCss).toMatch(/\.topbar\.is-hidden\s*\{[^}]*visibility:\s*hidden/)
  })
})
