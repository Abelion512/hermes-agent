import { Chalk } from 'chalk'

import { INLINE_RE } from '../components/markdown.js'
import type { Theme } from '../theme.js'

import { applyMathBoxFormat, texToUnicode } from './mathUnicode.js'

// Provide a pre-configured Chalk instance with truecolor forced ON so it doesn't
// drop colors when run inside Ink context (which sometimes overrides FORCE_COLOR).
const ctx = new Chalk({ level: 3 })

function applyColor(text: string, color?: string, bg?: string): string {
  let c = ctx

  if (bg) {
    if (bg.startsWith('ansi256(')) {c = c.bgAnsi256(parseInt(bg.slice(8, -1), 10))}
    else if (bg.startsWith('rgb(')) {
      const match = bg.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/)

      if (match) {c = c.bgRgb(parseInt(match[1]!, 10), parseInt(match[2]!, 10), parseInt(match[3]!, 10))}
    }
    else {c = c.bgHex(bg)}
  }

  if (color) {
    if (color.startsWith('ansi256(')) {c = c.ansi256(parseInt(color.slice(8, -1), 10))}
    else if (color.startsWith('rgb(')) {
      const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/)

      if (match) {c = c.rgb(parseInt(match[1]!, 10), parseInt(match[2]!, 10), parseInt(match[3]!, 10))}
    }
    else {c = c.hex(color)}
  }

  return c(text)
}

export function formatToAnsi(text: string, t: Theme): string {
  let result = ''
  let last = 0

  for (const m of text.matchAll(INLINE_RE)) {
    const i = m.index ?? 0

    if (i > last) {
      result += text.slice(last, i)
    }

    if (m[1] && m[2]) {
      result += applyColor(`[image: ${m[1]}] ${m[2]}`, t.color.muted)
    } else if (m[3] && m[4]) {
      // MdInline fallback styling
      result += applyColor(m[3], t.color.text)
    } else if (m[5]) {
      // MdInline fallback styling
      result += applyColor(m[5], t.color.text)
    } else if (m[6]) {
      result += ctx.strikethrough(formatToAnsi(m[6], t))
    } else if (m[7]) {
      result += applyColor(ctx.dim(m[7]), t.color.accent)
    } else if (m[8] ?? m[9]) {
      result += ctx.bold(formatToAnsi(m[8] ?? m[9]!, t))
    } else if (m[10] ?? m[11]) {
      result += ctx.italic(formatToAnsi(m[10] ?? m[11]!, t))
    } else if (m[12]) {
      result += applyColor(formatToAnsi(m[12], t), t.color.diffAddedWord, t.color.diffAdded)
    } else if (m[13]) {
      result += applyColor(`[${m[13]}]`, t.color.muted)
    } else if (m[14]) {
      result += applyColor(`^${m[14]}`, t.color.muted)
    } else if (m[15]) {
      result += applyColor(`_${m[15]}`, t.color.muted)
    } else if (m[16]) {
      result += applyColor(m[16], t.color.text)
    } else if (m[17] ?? m[18]) {
      const mathCode = m[17] ?? m[18]!
      let mathText = texToUnicode(mathCode)

      mathText = applyMathBoxFormat(
        mathText,
        t => t,
        box => ctx.bold.inverse(` ${box} `)
      ).join('')

      result += applyColor(mathText, t.color.accent)
    }

    last = i + m[0].length
  }

  if (last < text.length) {
    result += text.slice(last)
  }

  return result
}
