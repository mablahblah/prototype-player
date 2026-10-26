// Section shortcut nav: highlights the section being read, and scrolls to a section when its link is clicked.
// On narrow screens it is a strip of dashes. It opens on hover, tap, keyboard focus, or a finger drag (Hammer.js), and a name can only be chosen once the menu is fully open.
const nav = document.querySelector('.section-nav')
if (nav) {
  const links = [...nav.querySelectorAll('a')]
  const sections = links.map((a) => document.getElementById(a.dataset.target))
  const navHeight = () => document.querySelector('header[class*="_bar_"]')?.offsetHeight ?? 0
  const narrow = matchMedia('(max-width: 1100px)')
  const reduceMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches
  const SLIDE_MS = 260
  const DRAG_DISTANCE = 160

  let shown = -1
  let peekTimer
  let settleTimer
  let jumpOpen = false
  let hoveringWithMouse = false

  // Menu state: closed, opening (sliding out, names not yet clickable), open, closing.
  function setState(state) {
    nav.dataset.state = state
  }
  setState('closed')

  function openMenu() {
    if (nav.dataset.state === 'open' || nav.dataset.state === 'opening') return
    clearPeek()
    nav.style.removeProperty('--reveal')
    setState('opening')
    clearTimeout(settleTimer)
    settleTimer = setTimeout(() => setState('open'), reduceMotion() ? 0 : SLIDE_MS)
  }

  function closeMenu() {
    clearTimeout(settleTimer)
    nav.style.removeProperty('--reveal')
    setState('closed')
    if (nav.contains(document.activeElement)) document.activeElement.blur()
  }

  // Scrolling into a new section slides out only that section's name, briefly.
  function peek(link) {
    clearPeek()
    link.classList.add('is-peek')
    peekTimer = setTimeout(clearPeek, 1500)
  }

  function clearPeek() {
    clearTimeout(peekTimer)
    links.forEach((a) => a.classList.remove('is-peek'))
  }

  function update() {
    // The current section is the last one whose top has passed a line a third of the way down the window.
    const line = navHeight() + innerHeight / 3
    let current = 0
    sections.forEach((section, n) => {
      // A chapter inside the pinned panel counts once the panel has scrolled to it, not a third of a screen early.
      const reached = section.hasAttribute('data-nav-pinned') ? navHeight() + 2 : line
      if (section.getBoundingClientRect().top <= reached) current = n
    })
    links.forEach((a, n) => a.setAttribute('aria-current', String(n === current)))
    // Not during a jump the reader chose from the nav: they already know where they are going.
    const jumping = document.documentElement.hasAttribute('data-nav-scrolling')
    if (shown !== -1 && current !== shown && narrow.matches && !jumping && nav.dataset.state === 'closed') peek(links[current])
    shown = current
  }

  function jumpTo(n) {
    const top = sections[n].getBoundingClientRect().top + scrollY - navHeight()
    freezePiecesUntilStill()
    scrollTo({ top: n === 0 ? 0 : top, behavior: reduceMotion() ? 'auto' : 'smooth' })
  }

  links.forEach((a, n) => {
    a.addEventListener('click', (event) => {
      // Handled here rather than by the address, which holds the Shallow/Deep choice.
      event.preventDefault()
      if (!narrow.matches) return jumpTo(n)
      // A tap on the closed strip opens it; a name only counts once the menu has finished sliding out.
      if (nav.dataset.state !== 'open') return openMenu()
      jumpOpen = true
      jumpTo(n)
    })
  })

  // A tap on the strip between dashes opens it too.
  nav.addEventListener('click', (event) => {
    if (narrow.matches && !event.target.closest('a')) openMenu()
  })

  // Hover opens and closes it, for a mouse only; a touch screen's pretend hover would fight the taps.
  nav.addEventListener('pointerenter', (event) => {
    if (event.pointerType !== 'mouse' || !narrow.matches) return
    hoveringWithMouse = true
    openMenu()
  })
  nav.addEventListener('pointerleave', (event) => {
    if (event.pointerType !== 'mouse' || !narrow.matches) return
    hoveringWithMouse = false
    if (!jumpOpen) closeMenu()
  })

  // Tapping or clicking anywhere outside the menu closes it.
  document.addEventListener('pointerdown', (event) => {
    if (!narrow.matches || nav.dataset.state === 'closed' || jumpOpen) return
    if (!nav.contains(event.target)) closeMenu()
  }, true)

  // Keyboard users open it by tabbing in; it is fully open at once so Enter works straight away.
  nav.addEventListener('focusin', (event) => {
    if (narrow.matches && event.target.matches(':focus-visible')) {
      clearTimeout(settleTimer)
      setState('open')
    }
  })
  nav.addEventListener('focusout', (event) => {
    if (narrow.matches && !nav.contains(event.relatedTarget) && !hoveringWithMouse && !jumpOpen) closeMenu()
  })

  // Finger drag: the names follow the finger out, and pushing left slides them back in. Letting go past halfway, or with a flick, finishes the move.
  if (window.Hammer) {
    const hammer = new Hammer.Manager(nav, { touchAction: 'pan-y' })
    hammer.add(new Hammer.Pan({ direction: Hammer.DIRECTION_HORIZONTAL, threshold: 4 }))
    let startReveal = 0
    let reveal = 0
    hammer.on('panstart', () => {
      if (!narrow.matches || jumpOpen) return
      clearPeek()
      clearTimeout(settleTimer)
      startReveal = nav.dataset.state === 'closed' ? 0 : 1
      nav.classList.add('is-dragging')
    })
    hammer.on('panmove', (event) => {
      if (!nav.classList.contains('is-dragging')) return
      reveal = Math.min(1, Math.max(0, startReveal + event.deltaX / DRAG_DISTANCE))
      nav.style.setProperty('--reveal', reveal.toFixed(3))
    })
    hammer.on('panend pancancel', (event) => {
      if (!nav.classList.contains('is-dragging')) return
      nav.classList.remove('is-dragging')
      const flick = Math.abs(event.velocityX) > 0.3 ? Math.sign(event.velocityX) : 0
      const shouldOpen = flick ? flick > 0 : reveal > 0.5
      nav.style.removeProperty('--reveal')
      if (shouldOpen) {
        setState('opening')
        settleTimer = setTimeout(() => setState('open'), reduceMotion() ? 0 : SLIDE_MS)
      } else {
        closeMenu()
      }
    })
  }

  // Freezes the work pieces for the length of a jump, and lets them update again once the page has stopped moving.
  function freezePiecesUntilStill() {
    const root = document.documentElement
    root.setAttribute('data-nav-scrolling', '')
    let lastY = -1
    let stillFor = 0
    const timer = setInterval(() => {
      stillFor = scrollY === lastY ? stillFor + 1 : 0
      lastY = scrollY
      if (stillFor >= 3) {
        clearInterval(timer)
        root.removeAttribute('data-nav-scrolling')
        dispatchEvent(new Event('navscrollend'))
      }
    }, 50)
  }

  // After a click the menu stays open until the jump has finished, then closes unless the mouse is still over it.
  addEventListener('navscrollend', () => {
    if (!jumpOpen) return
    jumpOpen = false
    if (!hoveringWithMouse) closeMenu()
  })

  addEventListener('scroll', update, { passive: true })
  addEventListener('resize', update)
  document.querySelectorAll('.depth-toggle button').forEach((b) => b.addEventListener('click', update))
  update()
}
