// Swaps between the Shallow and Deep versions of the page. The choice sits in the address (#shallow or #deep) so a reload or a shared link keeps it.
const buttons = document.querySelectorAll('.depth-toggle button')

function show(depth) {
  for (const view of document.querySelectorAll('.depth-view')) view.hidden = view.id !== 'depth-' + depth
  for (const b of buttons) b.setAttribute('aria-pressed', String(b.dataset.depth === depth))
}

for (const b of buttons) {
  b.addEventListener('click', () => {
    history.replaceState(null, '', '#' + b.dataset.depth)
    show(b.dataset.depth)
  })
}

show(location.hash === '#shallow' ? 'shallow' : 'deep')
