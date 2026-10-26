// Scroll-driven work beats: the section is several screens tall and its panel sticks in place, so scrolling through it only changes which piece of work is showing. One panel can hold several chapters; the title beside the pieces follows whichever chapter the current piece belongs to.
for (const section of document.querySelectorAll('.beats')) {
  const beats = [...section.querySelectorAll('.beat')]
  const dots = [...section.querySelectorAll('.beat-dot')]
  const sticky = section.querySelector('.beats-sticky')
  const title = section.querySelector('.beats-title')
  const sub = section.querySelector('.beats-sub')
  let current = -1

  function update() {
    // While a section-nav jump is scrolling past, pieces stay frozen so they do not flick by.
    if (document.documentElement.hasAttribute('data-nav-scrolling')) return
    const scrollable = section.offsetHeight - sticky.offsetHeight
    const scrolled = -section.getBoundingClientRect().top + parseFloat(getComputedStyle(sticky).top)
    const progress = Math.min(Math.max(scrolled / scrollable, 0), 0.9999)
    const index = Math.floor(progress * beats.length)
    if (index === current) return
    current = index
    const chapter = beats[index].dataset.title
    beats.forEach((beat, n) => {
      beat.classList.toggle('is-active', n === index)
      beat.classList.toggle('is-past', n < index)
    })
    dots.forEach((dot, n) => {
      dot.classList.toggle('is-active', n === index)
      dot.classList.toggle('is-other-chapter', !!chapter && beats[n].dataset.title !== chapter)
    })
    if (chapter) swapText(title, chapter)
    swapText(sub, beats[index].dataset.sub)
  }

  // Swaps a label's text, fading only when the text actually changes.
  function swapText(el, text) {
    if (!el || el.textContent === text) return
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || !el.textContent) {
      el.textContent = text
      return
    }
    el.classList.add('is-changing')
    setTimeout(() => {
      el.textContent = text
      el.classList.remove('is-changing')
    }, 250)
  }

  addEventListener('scroll', update, { passive: true })
  addEventListener('navscrollend', () => { current = -1; update() })
  addEventListener('resize', update)
  // The section has no height while its view is hidden, so re-check when the depth toggle shows it.
  document.querySelectorAll('.depth-toggle button').forEach((b) => b.addEventListener('click', () => { current = -1; update() }))
  update()
}
