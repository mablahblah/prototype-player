const ORDER = ['Resting', 'Hover', 'Pressed']
const isOld = (color) => !color.name.startsWith('--gray-')

const chip = (color) => `
  <span class="chip">
    <span class="chip-swatch" style="background:${color.value}"></span>
    <code>${color.name}</code>
    <span class="chip-l">L ${color.l}%</span>
  </span>`

// One copy of the piece per state, in the state's fill.
const piece = (row, colors, decided) => {
  const fills = { ...colors.states, [row.state]: decided }
  return ORDER.map((state) => {
    const fill = fills[state]
    const isDecided = state === row.state
    const keptOld = !isDecided && isOld(fill) && colors === row.swapped
    const label = `${state}${keptOld ? ' (today)' : ''}`
    const button =
      row.piece === 'solid'
        ? `<span class="solid" style="background:${fill.value};color:${colors.text.value}">
             <span class="solid-icon">${window.ICONS.figma}</span>Try Prototype</span>`
        : `<span class="back" style="background:${fill.value};color:${colors.text.value}">
             <span class="back-icon">${window.ICONS.back}</span>BACK</span>`
    return `
      <figure class="state${isDecided ? ' state-decided' : ''}">
        ${button}
        <figcaption>${label}</figcaption>
      </figure>`
  }).join('')
}

const column = (row, heading, colors, decided) => `
  <div class="column">
    <h4>${heading}</h4>
    ${chip(decided)}
    <div class="stage" style="background:${colors.page.value}">
      ${piece(row, colors, decided)}
    </div>
  </div>`

const swatches = (colors) =>
  colors
    .map(
      (c) => `
  <li>
    <span class="swatch" style="background:${c.value}"></span>
    <code>${c.name}</code>
    <span class="value">${c.shown ?? c.value}</span>
  </li>`,
    )
    .join('')

document.getElementById('palette').innerHTML = swatches(window.GRAYS)
document.getElementById('blue-green').innerHTML = swatches(window.BLUE_GREEN)

document.getElementById('rows').innerHTML = window.ROWS.map(
  (row) => `
  <section class="row" aria-labelledby="row-${row.old.name}">
    <h2 id="row-${row.old.name}"><code>${row.old.name}</code> <span class="row-l">L ${row.old.l}%</span></h2>
    <h3>${row.pieceName}</h3>
    ${
      row.alsoUsedBy.length
        ? `<p class="also">Also uses it: ${row.alsoUsedBy.join('; ')}.</p>`
        : '<p class="also">Nothing else uses it.</p>'
    }
    <div class="columns">
      ${column(row, 'Today', row.today, row.old)}
      ${row.options.map((option) => column(row, `Swap to ${option.name}`, row.swapped, option)).join('')}
    </div>
  </section>`,
).join('')
