import { useEffect, useRef, useCallback } from 'react'
import * as d3 from 'd3'
import type { GraphEdge, NavNode } from '../data/types'
import type { NextNodeItem } from '../store/navStore'

export interface NavCanvasData {
  allNodes?: NavNode[]
  allEdges?: GraphEdge[]
  currentNode?: NavNode | null
  prevNodes?: NextNodeItem[]
  nextNodes?: NextNodeItem[]
  waypointIds?: Set<string>
  /** 全览视图中当前选中节点的 id */
  selectedNodeId?: string | null
  /** 子图节点 id 集合（在全览中显示特殊样式） */
  subGraphNodeIds?: Set<string>
  /** 引用节点 id 集合（在全览中显示虚线样式） */
  refNodeIds?: Set<string>
}

export interface NavCanvasOptions {
  onNodeClick?: (node: NavNode) => void
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string
  label: string
  ref: NavNode
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  weight: number
}

const ACCENT = '#06b6d4'
const ACCENT_SOFT = 'rgba(6,182,212,.35)'
const ACCENT2 = '#14b8a6'
const WAYPOINT = '#ffd230'

/**
 * 统一 D3 Hook：力导向全览 + DAG 逐站双模式。
 * 内部维护两个独立渲染实例，mode 切换时切换 SVG group 可见性，互不销毁。
 */
export function useNavCanvas(
  containerRef: React.RefObject<HTMLDivElement | null>,
  mode: 'overview' | 'station',
  data: NavCanvasData,
  options: NavCanvasOptions,
) {
  const svgRef = useRef<d3.Selection<SVGSVGElement, unknown, null, undefined> | null>(null)
  const rootGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null)
  const overviewGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null)
  const stationGRef = useRef<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null)
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null)
  const overviewBuiltRef = useRef(false)
  const overviewDataVersionRef = useRef('')
  const nodeSelRef = useRef<d3.Selection<SVGGElement, SimNode, SVGGElement, unknown> | null>(null)

  const dataRef = useRef(data)
  dataRef.current = data
  const optionsRef = useRef(options)
  optionsRef.current = options

  /* ---------- 初始化 SVG 骨架（仅一次） ---------- */
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .style('display', 'block')
      .style('touch-action', 'none')

    // 点网格背景
    const defs = svg.append('defs')
    const pat = defs
      .append('pattern')
      .attr('id', 'nc-dot-grid')
      .attr('width', 28)
      .attr('height', 28)
      .attr('patternUnits', 'userSpaceOnUse')
    pat.append('circle').attr('cx', 14).attr('cy', 14).attr('r', 0.8).attr('fill', '#334155').attr('opacity', 0.5)
    defs
      .append('marker')
      .attr('id', 'nc-arrow')
      .attr('viewBox', '0 -4 8 8')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4 L8,0 L0,4')
      .attr('fill', ACCENT)
      .attr('opacity', 0.55)

    svg.append('rect').attr('width', '100%').attr('height', '100%').attr('fill', 'url(#nc-dot-grid)')

    const rootG = svg.append('g')
    const overviewG = rootG.append('g')
    const stationG = rootG.append('g')

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.4, 3])
      .on('zoom', (e) => rootG.attr('transform', e.transform))
    svg.call(zoom)

    svgRef.current = svg
    rootGRef.current = rootG
    overviewGRef.current = overviewG
    stationGRef.current = stationG
    zoomRef.current = zoom

    // resize：debounce 200ms 重绘
    let timer: ReturnType<typeof setTimeout> | null = null
    const ro = new ResizeObserver(() => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        renderStation()
        const d = dataRef.current
        if (simRef.current && d.allNodes) {
          const { clientWidth: w, clientHeight: h } = container
          simRef.current.force('center', d3.forceCenter(w / 2, h / 2))
          simRef.current.alpha(0.1).restart()
        }
      }, 200)
    })
    ro.observe(container)

    return () => {
      ro.disconnect()
      if (timer) clearTimeout(timer)
      simRef.current?.stop()
      svg.remove()
      svgRef.current = null
      overviewBuiltRef.current = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ---------- 全览：构建力导向图（仅首次进入 overview 时） ---------- */
  const buildOverview = useCallback(() => {
    const container = containerRef.current
    const overviewG = overviewGRef.current
    const d = dataRef.current
    if (!container || !overviewG || !d.allNodes || !d.allEdges) return
    if (d.allNodes.length === 0) return
    if (overviewBuiltRef.current) return
    overviewBuiltRef.current = true

    const w = container.clientWidth
    const h = container.clientHeight

    const nodes: SimNode[] = d.allNodes.map((n) => ({ id: n.id, label: n.label, ref: n }))
    const links: SimLink[] = d.allEdges.map((e) => ({ source: e.source, target: e.target, weight: e.weight }))

    const linkSel = overviewG
      .append('g')
      .selectAll<SVGPathElement, SimLink>('path')
      .data(links)
      .enter()
      .append('path')
      .attr('fill', 'none')
      .attr('stroke', (l) => (l.weight >= 0.7 ? ACCENT : ACCENT2))
      .attr('stroke-opacity', (l) => (l.weight >= 0.7 ? 0.5 : 0.28))
      .attr('stroke-width', (l) => Math.max(0.8, l.weight * 2.4))
      .attr('stroke-dasharray', (l) => (l.weight < 0.5 ? '4 3' : null))
      .attr('marker-end', 'url(#nc-arrow)')

    const nodeSel = overviewG
      .append('g')
      .selectAll<SVGGElement, SimNode>('g')
      .data(nodes)
      .enter()
      .append('g')
      .style('cursor', 'grab')

    nodeSel.append('circle').attr('class', 'nc-halo').attr('r', 18).attr('fill', ACCENT2).attr('opacity', 0.25)
    nodeSel
      .append('circle')
      .attr('class', 'nc-body')
      .attr('r', 24)
      .attr('fill', '#1e293b')
      .attr('stroke', ACCENT2)
      .attr('stroke-width', 2.5)
    nodeSel
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 40)
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .attr('font-weight', 500)
      .text((n) => n.label)

    const sim = d3
      .forceSimulation<SimNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((n) => n.id)
          .distance((l) => (l.weight >= 0.7 ? 150 : 190))
          .strength((l) => l.weight * 0.4),
      )
      .force('charge', d3.forceManyBody().strength(-380))
      .force('center', d3.forceCenter(w / 2, h / 2))
      .force('collide', d3.forceCollide().radius(52))
      .force('x', d3.forceX(w / 2).strength(0.06))
      .force('y', d3.forceY(h / 2).strength(0.06))

    sim.on('tick', () => {
      linkSel.attr('d', (l) => {
        const s = l.source as SimNode
        const t = l.target as SimNode
        const dx = (t.x ?? 0) - (s.x ?? 0)
        const dy = (t.y ?? 0) - (s.y ?? 0)
        const dr = Math.sqrt(dx * dx + dy * dy) * 1.2
        return `M${s.x},${s.y} A${dr},${dr} 0 0,1 ${t.x},${t.y}`
      })
      nodeSel.attr('transform', (n) => `translate(${n.x},${n.y})`)
    })

    // 预热 300 tick，之后低速运行避免抖动
    sim.stop()
    for (let i = 0; i < 300; i++) sim.tick()
    sim.alpha(0.1).alphaDecay(0.02).restart()

    simRef.current = sim
    nodeSelRef.current = nodeSel

    // ── 节点拖拽（d3.drag）：长按拖拽单个节点，其他节点受力学约束位移 ──
    const dragHandler = d3.drag<SVGGElement, SimNode>()
      .on('start', function (event, d) {
        // 阻止事件冒泡到 SVG 的 zoom 行为，避免画布平移和节点拖拽同时触发
        event.sourceEvent.stopPropagation()
        if (!event.active) sim.alphaTarget(0.3).restart()
        // 固定该节点的位置（fx/fy），仿真不再自动移动它
        d.fx = d.x
        d.fy = d.y
        // 光标样式切换为抓取中
        d3.select(this).style('cursor', 'grabbing')
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', function (event, _d) {
        if (!event.active) sim.alphaTarget(0)
        // 保持 fx/fy 不释放，节点停留在拖拽终点位置
        d3.select(this).style('cursor', 'grab')
      })
    nodeSel.call(dragHandler)

    // 点击选中节点（d3.drag 自动抑制拖拽过程中的 click 事件）
    nodeSel.on('click', (_e, n) => {
      optionsRef.current.onNodeClick?.(n.ref)
    })

    applyNodeStyles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [containerRef])

  /* ---------- 逐站：DAG 三层布局 ---------- */
  const renderStation = useCallback(() => {
    const container = containerRef.current
    const stationG = stationGRef.current
    if (!container || !stationG) return
    const d = dataRef.current
    stationG.selectAll('*').remove()
    if (!d.currentNode) return

    const w = container.clientWidth
    const h = container.clientHeight
    const cx = w / 2
    const cy = h * 0.46
    const layerGap = Math.min(120, h * 0.28)
    const topY = cy - layerGap
    const botY = cy + layerGap

    const prevs = (d.prevNodes ?? []).map((item, i, arr) => ({
      item,
      x: (w / (arr.length + 1)) * (i + 1),
      y: botY,
    }))
    const nexts = (d.nextNodes ?? []).map((item, i, arr) => ({
      item,
      x: (w / (arr.length + 1)) * (i + 1),
      y: topY,
    }))

    // 边：prev → current → next
    const edges = [
      ...prevs.map((p) => ({ x1: p.x, y1: p.y, x2: cx, y2: cy, w: p.item.ref.weight, weak: false })),
      ...nexts.map((n) => ({ x1: cx, y1: cy, x2: n.x, y2: n.y, w: n.item.ref.weight, weak: n.item.ref.source === 'browse' })),
    ]

    stationG
      .selectAll('path.edge')
      .data(edges)
      .enter()
      .append('path')
      .attr('fill', 'none')
      .attr('stroke', (e) => (e.weak ? 'rgba(6,182,212,.3)' : ACCENT))
      .attr('stroke-width', (e) => (e.weak ? 1 : 1.2 + e.w * 1.6))
      .attr('stroke-dasharray', (e) => (e.weak ? '5 4' : null))
      .attr('marker-end', 'url(#nc-arrow)')
      .attr('d', (e) => {
        const my = (e.y1 + e.y2) / 2
        return `M${e.x1},${e.y1} C${e.x1},${my} ${e.x2},${my} ${e.x2},${e.y2}`
      })
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .attr('opacity', 1)

    const drawNode = (
      x: number,
      y: number,
      node: NavNode,
      r: number,
      opts: { current?: boolean; weight?: number; dim?: boolean },
    ) => {
      const g = stationG.append('g').attr('transform', `translate(${x},${y})`).style('cursor', 'pointer')
      if (opts.current) {
        g.append('circle').attr('r', r + 8).attr('fill', 'none').attr('stroke', ACCENT_SOFT).attr('stroke-width', 2)
      }
      g.append('circle')
        .attr('r', r)
        .attr('fill', opts.current ? '#0e2a33' : '#1e293b')
        .attr('stroke', opts.current ? ACCENT : ACCENT2)
        .attr('stroke-width', opts.current ? 3 : 2)
        .attr('opacity', opts.dim ? 0.75 : 1)
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', 4)
        .attr('fill', 'rgba(255,255,255,.84)')
        .attr('font-size', opts.current ? '12px' : '10px')
        .attr('font-weight', 600)
        .text(node.label.length > 6 ? `${node.label.slice(0, 6)}…` : node.label)
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', r + 14)
        .attr('fill', '#94a3b8')
        .attr('font-size', '9px')
        .text(opts.weight != null ? `w ${opts.weight.toFixed(2)}` : opts.current ? '当前节点' : '')
      g.on('click', () => optionsRef.current.onNodeClick?.(node))
    }

    prevs.forEach((p) => drawNode(p.x, p.y, p.item.node, 22, { weight: p.item.ref.weight, dim: true }))
    drawNode(cx, cy, d.currentNode, 32, { current: true })
    nexts.forEach((n) => drawNode(n.x, n.y, n.item.node, 24, { weight: n.item.ref.weight }))
  }, [containerRef])

  /* ---------- 节点三态样式：普通 / 途经点 / 当前选中（spec §2） ---------- */
  const applyNodeStyles = useCallback(() => {
    const nodeSel = nodeSelRef.current
    if (!nodeSel) return
    const ids = dataRef.current.waypointIds ?? new Set<string>()
    const selectedId = dataRef.current.selectedNodeId ?? null
    const subIds = dataRef.current.subGraphNodeIds ?? new Set<string>()
    const refIds = dataRef.current.refNodeIds ?? new Set<string>()

    // body 圆圈：选中 > 途经点 > 普通
    nodeSel.select<SVGCircleElement>('circle.nc-body')
      .attr('fill', (n) => (n.id === selectedId ? '#0e2a33' : '#1e293b'))
      .attr('stroke', (n) => {
        if (n.id === selectedId) return ACCENT
        if (ids.has(n.id)) return WAYPOINT
        if (refIds.has(n.id)) return '#a78bfa' // 紫色表示引用节点
        return ACCENT2
      })
      .attr('stroke-width', (n) => {
        if (n.id === selectedId || ids.has(n.id)) return 4
        return 2.5
      })
      .attr('stroke-dasharray', (n) => {
        if (refIds.has(n.id)) return '6 3' // 引用节点虚线
        if (subIds.has(n.id)) return '4 3'  // 子图节点虚线
        return null
      })

    // halo 光晕
    nodeSel.select<SVGCircleElement>('circle.nc-halo')
      .attr('r', (n) => (n.id === selectedId ? 24 : 18))
      .attr('fill', (n) => {
        if (n.id === selectedId) return ACCENT
        if (ids.has(n.id)) return WAYPOINT
        if (refIds.has(n.id)) return '#a78bfa'
        return ACCENT2
      })
      .attr('opacity', (n) => {
        if (n.id === selectedId) return 0.3
        if (ids.has(n.id)) return 0.4
        return 0.25
      })

    // 子图节点标识：文件夹图标
    nodeSel.select<SVGTextElement>('text.nc-subgraph-icon').remove()
    nodeSel.each(function (n) {
      if (!subIds.has(n.id)) return
      const g = d3.select(this)
      g.append('text')
        .attr('class', 'nc-subgraph-icon')
        .attr('text-anchor', 'middle')
        .attr('dy', -26)
        .attr('fill', '#ffd230')
        .attr('font-size', '10px')
        .text('📂')
    })

    // 引用节点标识：来源图标签
    nodeSel.select<SVGTextElement>('text.nc-ref-label').remove()
    nodeSel.each(function (n) {
      if (!refIds.has(n.id)) return
      const g = d3.select(this)
      const refNode = n.ref as any
      const srcLabel = refNode?._sourceGraphLabel || refNode?._sourceGraphId || ''
      g.append('text')
        .attr('class', 'nc-ref-label')
        .attr('text-anchor', 'middle')
        .attr('dy', 54)
        .attr('fill', '#a78bfa')
        .attr('font-size', '8px')
        .text(`↻ ${srcLabel}`)
    })

    // 脉冲环：选中节点添加（CSS 动画驱动），非选中移除
    nodeSel.each(function (n) {
      const g = d3.select(this)
      const existing = g.select<SVGCircleElement>('circle.nc-pulse')
      if (n.id === selectedId) {
        if (existing.empty()) {
          g.insert('circle', ':first-child').attr('class', 'nc-pulse').attr('r', 36)
        }
      } else {
        existing.remove()
      }
    })
  }, [])

  /* ---------- 模式切换：可见性 + 按需构建/重绘 ---------- */

  /* 画布核心数据变化时，重置全览重建标志，触发 D3 重建 */
  useEffect(() => {
    if (mode !== 'overview') return
    const d = dataRef.current
    const key = `${d.allNodes?.length ?? 0}:${d.allEdges?.length ?? 0}`
    if (overviewDataVersionRef.current && overviewDataVersionRef.current !== key) {
      // 清除旧 D3 元素 + 停止旧仿真
      overviewGRef.current?.selectAll('*').remove()
      simRef.current?.stop()
      simRef.current = null
      overviewBuiltRef.current = false
    }
    overviewDataVersionRef.current = key
  }, [mode, data.allNodes?.length, data.allEdges?.length])

  useEffect(() => {
    overviewGRef.current?.style('display', mode === 'overview' ? 'inline' : 'none')
    stationGRef.current?.style('display', mode === 'station' ? 'inline' : 'none')
    if (mode === 'overview') {
      // data 从空→非空时会触发重入（allNodes.length 变化），因 overviewBuiltRef 仍为 false
      if (!overviewBuiltRef.current) buildOverview()
    } else {
      renderStation()
    }
  }, [mode, data.allNodes?.length, data.allEdges?.length, buildOverview, renderStation])

  /* ---------- 数据变化：逐站重绘 / 途径点高亮 ---------- */
  useEffect(() => {
    if (mode === 'station') renderStation()
  }, [mode, data.currentNode, data.prevNodes, data.nextNodes, renderStation])

  useEffect(() => {
    applyNodeStyles()
  }, [data.selectedNodeId, data.waypointIds, data.subGraphNodeIds, data.refNodeIds, applyNodeStyles])

  /* ---------- 缩放控制 ---------- */
  const zoomBy = useCallback((factor: number) => {
    const svg = svgRef.current
    const zoom = zoomRef.current
    if (!svg || !zoom) return
    svg.transition().duration(280).call(zoom.scaleBy, factor)
  }, [])

  const zoomIn = useCallback(() => zoomBy(1.3), [zoomBy])
  const zoomOut = useCallback(() => zoomBy(1 / 1.3), [zoomBy])
  const zoomReset = useCallback(() => {
    const svg = svgRef.current
    const zoom = zoomRef.current
    if (!svg || !zoom) return
    svg.transition().duration(280).call(zoom.transform, d3.zoomIdentity)
  }, [])

  return { zoomIn, zoomOut, zoomReset }
}
