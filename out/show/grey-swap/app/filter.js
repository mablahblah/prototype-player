// The home page's filter pill in each of its states, drawn with the colors the
// site will have after the swap. Values copied from styles/design-tokens.css,
// and the blue-green steps from the prototype's lightness scale
// (prototypes/home-screen-work-categories/src/color/generate.ts).

const C = {
  gray0: 'oklch(99.5% 0.001 78)',
  gray0at45: 'oklch(99.5% 0.001 78 / 0.45)',
  gray100: 'oklch(95% 0.006 78)',
  gray200: 'oklch(91% 0.011 78)',
  gray600: 'oklch(50% 0.012 78)',
  gray950: 'oklch(17% 0.012 78)',
  blueGreen100: 'oklch(76% 0.091 205)',
  blueGreenOffset: 'oklch(68% 0.091 185)',
  blueGreen110: 'oklch(72.6% 0.087 205)',
  blueGreen120: 'oklch(69.2% 0.083 205)',
  blueGreen140: 'oklch(62.4% 0.075 205)',
  // What the site draws today: halfway between blue-green and its offset.
  todayMix: 'color-mix(in oklab, oklch(76% 0.091 205), oklch(68% 0.091 185))',
}

const FILTERS = ['Product Design', 'Builds']

// One pill. `chosen` is the chosen filter's shape color; `other` is the fill
// and word color of the filter that isn't chosen; `onColor` draws the copy
// that sits inside the sweep's blue-green sliver.
const pill = ({ chosen = C.blueGreen100, other = null, onColor = false } = {}) => {
  const border = onColor ? C.gray0at45 : C.gray200
  const items = FILTERS.map((label, i) => {
    if (i === 0) {
      const shape = onColor ? C.gray0 : chosen
      const words = onColor ? C.blueGreen100 : C.gray0
      return `<span class="filter-item" style="background:${shape};color:${words}">${label}</span>`
    }
    const fill = other ? other.fill : 'transparent'
    const words = onColor ? C.gray0 : other ? C.gray600 : C.gray950
    return `<span class="filter-item" style="background:${fill};color:${words}">${label}</span>`
  }).join('')
  return `<span class="filter-track" style="border-color:${border}"><span class="filter-inside">${items}</span></span>`
}

const state = (label, html, decided = false, sliver = false) => `
  <figure class="state${decided ? ' state-decided' : ''}">
    <span class="filter-stage${sliver ? ' filter-sliver' : ''}">${html}</span>
    <figcaption>${label}</figcaption>
  </figure>`

// The chosen filter's three states in one column.
const chosenColumn = (heading, states) => `
  <div class="column">
    <h4>${heading}</h4>
    <div class="stage stage-column" style="background:${C.gray0}">
      ${states
        .map(
          ([label, name, value]) => `
        <span class="chip">
          <span class="chip-swatch" style="background:${value}"></span>
          <code>${name}</code>
        </span>
        ${state(label, pill({ chosen: value }))}`,
        )
        .join('')}
    </div>
  </div>`

document.getElementById('filter').innerHTML = `
  <section class="row" aria-labelledby="filter-heading">
    <h2 id="filter-heading">The filter pill</h2>
    <h3>Every state, after the swap</h3>
    <p class="also">The chosen filter is drawn at the proposed steps: <code>--brand-blue-green-100</code> resting, <code>-120</code> under the mouse, <code>-140</code> pressed.</p>
    <div class="stage stage-wrap" style="background:${C.gray0}">
      ${state('Resting', pill())}
      ${state('Mouse on the chosen filter', pill({ chosen: C.blueGreen120 }))}
      ${state('Pressing the chosen filter', pill({ chosen: C.blueGreen140 }))}
      ${state('Mouse on the other filter', pill({ other: { fill: C.gray100 } }))}
      ${state('Pressing the other filter', pill({ other: { fill: C.gray200 } }))}
      ${state('The copy inside the sweep', pill({ onColor: true }), false, true)}
    </div>

    <h3 class="filter-compare-heading">The chosen filter, today and proposed</h3>
    <p class="also">Today the mouse state is a mix halfway between blue-green and its offset, and pressed is the offset. Proposed, all three are steps on blue-green's scale.</p>
    <div class="columns columns-two">
      ${chosenColumn('Today', [
        ['Resting', '--brand-blue-green', C.blueGreen100],
        ['Mouse on the chosen filter', 'mix', C.todayMix],
        ['Pressing the chosen filter', '--brand-blue-green-offset', C.blueGreenOffset],
      ])}
      ${chosenColumn('Proposed', [
        ['Resting', '--brand-blue-green-100', C.blueGreen100],
        ['Mouse on the chosen filter', '--brand-blue-green-120', C.blueGreen120],
        ['Pressing the chosen filter', '--brand-blue-green-140', C.blueGreen140],
      ])}
    </div>
  </section>`
