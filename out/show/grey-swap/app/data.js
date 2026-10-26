// Every color here is copied from styles/design-tokens.css as it stands.

// The new scale, lightest first.
window.GRAYS = [
  { name: '--gray-0', value: 'oklch(99.5% 0.001 78)', l: 99.5 },
  { name: '--gray-25', value: 'oklch(98.5% 0.002 78)', l: 98.5 },
  { name: '--gray-50', value: 'oklch(97.5% 0.003 78)', l: 97.5 },
  { name: '--gray-100', value: 'oklch(95% 0.006 78)', l: 95 },
  { name: '--gray-200', value: 'oklch(91% 0.011 78)', l: 91 },
  { name: '--gray-300', value: 'oklch(85% 0.012 78)', l: 85 },
  { name: '--gray-400', value: 'oklch(72% 0.012 78)', l: 72 },
  { name: '--gray-500', value: 'oklch(60% 0.012 78)', l: 60 },
  { name: '--gray-600', value: 'oklch(50% 0.012 78)', l: 50 },
  { name: '--gray-700', value: 'oklch(40% 0.012 78)', l: 40 },
  { name: '--gray-800', value: 'oklch(30% 0.012 78)', l: 30 },
  { name: '--gray-900', value: 'oklch(23% 0.012 78)', l: 23 },
  { name: '--gray-950', value: 'oklch(17% 0.012 78)', l: 17 },
]

// Blue-green's scale, from the prototype's lightnessScales
// (prototypes/home-screen-work-categories/src/color/generate.ts): 100 is the
// brand color, each step 3.4 points of lightness, lower numbers lighter.
window.BLUE_GREEN = [
  { name: '--brand-blue-green-50', value: 'oklch(93% 0.051 205)' },
  { name: '--brand-blue-green-60', value: 'oklch(89.6% 0.076 205)' },
  { name: '--brand-blue-green-70', value: 'oklch(86.2% 0.103 205)' },
  { name: '--brand-blue-green-80', value: 'oklch(82.8% 0.099 205)' },
  { name: '--brand-blue-green-90', value: 'oklch(79.4% 0.095 205)' },
  { name: '--brand-blue-green-100', value: 'oklch(76% 0.091 205)' },
  { name: '--brand-blue-green-110', value: 'oklch(72.6% 0.087 205)' },
  { name: '--brand-blue-green-120', value: 'oklch(69.2% 0.083 205)' },
  { name: '--brand-blue-green-130', value: 'oklch(65.8% 0.079 205)' },
  { name: '--brand-blue-green-140', value: 'oklch(62.4% 0.075 205)' },
  { name: '--brand-blue-green-150', value: 'oklch(59% 0.071 205)' },
  { name: '--brand-blue-green-offset', value: 'oklch(68% 0.091 185)' },
  {
    name: '--brand-blue-green-gradient',
    value: 'linear-gradient(in oklch to bottom right, oklch(68% 0.091 185), oklch(76% 0.091 205))',
    shown: 'offset to 100',
  },
]

const gray = (name) => window.GRAYS.find((g) => g.name === name)

const OLD = {
  '--black-30': { name: '--black-30', value: 'oklch(76.28% 0.0034 17.23)', l: 76.3 },
  '--black-60': { name: '--black-60', value: 'oklch(50.69% 0.0051 17.32)', l: 50.7 },
  '--black-100': { name: '--black-100', value: 'oklch(17.88% 0.0016 17.31)', l: 17.9 },
  '--white-85': { name: '--white-85', value: 'oklch(88.38% 0.0022 17.2)', l: 88.4 },
  '--white-90': { name: '--white-90', value: 'oklch(92.27% 0.0011 17.18)', l: 92.3 },
  '--white-95': { name: '--white-95', value: 'oklch(97.02% 0 0)', l: 97 },
  '--white-100': { name: '--white-100', value: 'oklch(100% 0 0)', l: 100 },
}

// Each row: the old grey, the two new steps either side of it, and the piece
// of the site drawn with it. A piece is drawn in three states. `today` holds
// the colors the site uses now; `swapped` holds the clean one-for-one swaps of
// every other color in the piece, so the only thing that differs between the
// two option columns is the grey being decided.
window.ROWS = [
  {
    old: OLD['--black-30'],
    options: [gray('--gray-300'), gray('--gray-400')],
    piece: 'solid',
    pieceName: 'The Try Prototype button, pressed',
    state: 'Pressed',
    alsoUsedBy: [
      'Quote attribution text (--text-tertiary)',
      '--ui-caption-pointer, which nothing uses and is deleted',
    ],
    today: {
      page: OLD['--white-100'],
      text: OLD['--white-100'],
      states: { Resting: OLD['--black-100'], Hover: OLD['--black-60'] },
    },
    swapped: {
      page: gray('--gray-0'),
      text: gray('--gray-0'),
      states: { Resting: gray('--gray-950'), Hover: gray('--gray-600') },
    },
  },
  {
    old: OLD['--white-90'],
    options: [gray('--gray-100'), gray('--gray-200')],
    piece: 'back',
    pieceName: 'The Back button, under a resting mouse',
    state: 'Hover',
    alsoUsedBy: [
      'A top bar icon while pressed (--nav-item-bg-active)',
      "The work section gradient's bottom-left stop (--bg-work-bottom-left)",
    ],
    today: {
      page: OLD['--white-100'],
      text: OLD['--black-60'],
      states: { Resting: OLD['--white-95'], Pressed: OLD['--white-85'] },
    },
    swapped: {
      page: gray('--gray-0'),
      text: gray('--gray-600'),
      // Pressed is the next row's decision, so it keeps today's grey here.
      states: { Resting: gray('--gray-50'), Pressed: OLD['--white-85'] },
    },
  },
  {
    old: OLD['--white-85'],
    options: [gray('--gray-200'), gray('--gray-300')],
    piece: 'back',
    pieceName: 'The Back button, pressed',
    state: 'Pressed',
    alsoUsedBy: [],
    today: {
      page: OLD['--white-100'],
      text: OLD['--black-60'],
      states: { Resting: OLD['--white-95'], Hover: OLD['--white-90'] },
    },
    swapped: {
      page: gray('--gray-0'),
      text: gray('--gray-600'),
      // Hover is the row above's decision, so it keeps today's grey here.
      states: { Resting: gray('--gray-50'), Hover: OLD['--white-90'] },
    },
  },
]
