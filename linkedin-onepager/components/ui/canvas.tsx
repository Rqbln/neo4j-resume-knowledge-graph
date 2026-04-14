type CanvasCtx = CanvasRenderingContext2D & {
  running?: boolean
  frame?: number
}

const CONFIG = {
  friction: 0.5,
  trails: 80,
  size: 50,
  dampening: 0.025,
  tension: 0.99,
} as const

/** Stroke alpha tuned for light backgrounds; “lighter” stack was invisible behind UI + on pale pages. */
const STROKE_ALPHA = 0.32
const LINE_WIDTH = 9

class Oscillator {
  phase: number
  offset: number
  frequency: number
  amplitude: number
  private last = 0

  constructor(
    opts?: Partial<Pick<Oscillator, "phase" | "offset" | "frequency" | "amplitude">>
  ) {
    this.phase = opts?.phase ?? 0
    this.offset = opts?.offset ?? 0
    this.frequency = opts?.frequency ?? 0.001
    this.amplitude = opts?.amplitude ?? 1
  }

  update(): number {
    this.phase += this.frequency
    this.last = this.offset + Math.sin(this.phase) * this.amplitude
    return this.last
  }
}

class SpringNode {
  x = 0
  y = 0
  vy = 0
  vx = 0
}

class TrailLine {
  spring: number
  friction: number
  nodes: SpringNode[]

  constructor(spring: number, pos: { x: number; y: number }) {
    this.spring = spring + 0.1 * Math.random() - 0.05
    this.friction = CONFIG.friction + 0.01 * Math.random() - 0.005
    this.nodes = []
    for (let i = 0; i < CONFIG.size; i++) {
      const n = new SpringNode()
      n.x = pos.x
      n.y = pos.y
      this.nodes.push(n)
    }
  }

  update(pos: { x: number; y: number }): void {
    let spring = this.spring
    let t = this.nodes[0]
    t.vx += (pos.x - t.x) * spring
    t.vy += (pos.y - t.y) * spring
    for (let i = 0; i < this.nodes.length; i++) {
      t = this.nodes[i]
      if (i > 0) {
        const prev = this.nodes[i - 1]
        t.vx += (prev.x - t.x) * spring
        t.vy += (prev.y - t.y) * spring
        t.vx += prev.vx * CONFIG.dampening
        t.vy += prev.vy * CONFIG.dampening
      }
      t.vx *= this.friction
      t.vy *= this.friction
      t.x += t.vx
      t.y += t.vy
      spring *= CONFIG.tension
    }
  }

  draw(ctx: CanvasRenderingContext2D): void {
    let e: SpringNode
    let t: SpringNode
    let mx = this.nodes[0].x
    let my = this.nodes[0].y
    ctx.beginPath()
    ctx.moveTo(mx, my)
    const o = this.nodes.length - 2
    let a = 1
    for (; a < o; a++) {
      e = this.nodes[a]
      t = this.nodes[a + 1]
      mx = 0.5 * (e.x + t.x)
      my = 0.5 * (e.y + t.y)
      ctx.quadraticCurveTo(e.x, e.y, mx, my)
    }
    e = this.nodes[a]
    t = this.nodes[a + 1]
    ctx.quadraticCurveTo(e.x, e.y, t.x, t.y)
    ctx.stroke()
    ctx.closePath()
  }
}

function attachPointerHandlers(
  pos: { x: number; y: number },
  setPos: (x: number, y: number) => void
) {
  const onPointer = (e: MouseEvent | TouchEvent) => {
    if ("touches" in e && e.touches[0]) {
      setPos(e.touches[0].pageX, e.touches[0].pageY)
      e.preventDefault()
    } else if ("clientX" in e) {
      setPos(e.clientX, e.clientY)
    }
  }

  const onTouchStartOnly = (e: TouchEvent) => {
    if (e.touches.length === 1) {
      setPos(e.touches[0].pageX, e.touches[0].pageY)
    }
  }

  const onMouseMove = (e: MouseEvent) => onPointer(e)
  const onTouchMove = (e: TouchEvent) => onPointer(e)

  document.addEventListener("mousemove", onMouseMove)
  document.addEventListener("touchmove", onTouchMove, { passive: false })
  document.addEventListener("touchstart", onTouchStartOnly)

  return () => {
    document.removeEventListener("mousemove", onMouseMove)
    document.removeEventListener("touchmove", onTouchMove)
    document.removeEventListener("touchstart", onTouchStartOnly)
  }
}

/**
 * Interactive trailing lines (mousemove / touch).
 * Canvas must sit above backgrounds but use pointer-events: none so clicks pass through.
 */
export function renderCanvas(
  target: string | HTMLCanvasElement = "canvas"
): () => void {
  const canvas =
    typeof target === "string"
      ? (document.getElementById(target) as HTMLCanvasElement | null)
      : target

  if (!canvas) {
    return () => {}
  }

  const ctx = canvas.getContext("2d") as CanvasCtx | null
  if (!ctx) {
    return () => {}
  }

  ctx.running = true
  ctx.frame = 1

  const pos = { x: 0, y: 0 }
  let lines: TrailLine[] = []
  const hue = new Oscillator({
    phase: Math.random() * 2 * Math.PI,
    amplitude: 85,
    frequency: 0.0015,
    offset: 285,
  })

  let raf = 0

  const resetLines = () => {
    lines = []
    for (let i = 0; i < CONFIG.trails; i++) {
      lines.push(new TrailLine(0.45 + (i / CONFIG.trails) * 0.025, pos))
    }
  }

  const setPos = (x: number, y: number) => {
    pos.x = x
    pos.y = y
  }

  const resize = () => {
    canvas.width = window.innerWidth - 20
    canvas.height = window.innerHeight
    setPos(window.innerWidth / 2, window.innerHeight / 2)
    resetLines()
  }

  const loop = () => {
    if (!ctx.running) {
      return
    }
    ctx.globalCompositeOperation = "source-over"
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    const h = Math.round(hue.update())
    ctx.strokeStyle = `hsla(${h}, 88%, 52%, ${STROKE_ALPHA})`
    ctx.lineWidth = LINE_WIDTH
    ctx.lineCap = "round"
    ctx.lineJoin = "round"
    for (const line of lines) {
      line.update(pos)
      line.draw(ctx)
    }
    ctx.frame = (ctx.frame ?? 0) + 1
    raf = window.requestAnimationFrame(loop)
  }

  const onFocus = () => {
    if (!ctx.running) {
      ctx.running = true
      loop()
    }
  }

  const onBlur = () => {
    ctx.running = false
    window.cancelAnimationFrame(raf)
  }

  resize()

  const removePointer = attachPointerHandlers(pos, setPos)

  window.addEventListener("orientationchange", resize)
  window.addEventListener("resize", resize)
  window.addEventListener("focus", onFocus)
  window.addEventListener("blur", onBlur)

  loop()

  return () => {
    ctx.running = false
    window.cancelAnimationFrame(raf)
    removePointer()
    window.removeEventListener("orientationchange", resize)
    window.removeEventListener("resize", resize)
    window.removeEventListener("focus", onFocus)
    window.removeEventListener("blur", onBlur)
  }
}
