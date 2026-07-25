import React, { useEffect } from 'react'
import styles from './PlanView.module.css'
import Button from '../shared/Button'
import WaypointModeToggle from './WaypointModeToggle'
import PlanCard from './PlanCard'
import { usePlanStore } from '../../store/planStore'
import { useNavStore } from '../../store/navStore'
import { useBrowseStore } from '../../store/browseStore'
import { useViewStore } from '../../store/viewStore'

const PlanView: React.FC = () => {
  const {
    sourceWaypoints, waypointMode, plans, selectedPlanId,
    setWaypointMode, selectPlan, replan, enterBrowse, generatePlans,
  } = usePlanStore()
  const initFromSequence = useBrowseStore((s) => s.initFromSequence)
  const switchView = useViewStore((s) => s.switchView)

  // 直接从 TabBar 进入时：与 NavView 的途经点保持同步
  // （途经点序列有变化才重新生成，避免覆盖用户在规划页的模式/选中操作）
  useEffect(() => {
    const sync = () => {
      const navWps = useNavStore.getState().waypoints
      const cur = usePlanStore.getState().sourceWaypoints
      const changed =
        navWps.length !== cur.length || navWps.some((w, i) => cur[i]?.id !== w.id)
      if (changed && navWps.length >= 2) {
        const weightMode = navWps[0]?.priority_config?.mode ?? 'mixed'
        usePlanStore.getState().generatePlans(navWps, weightMode)
      } else if (changed && navWps.length < 2) {
        usePlanStore.getState().reset()
      }
    }
    sync()
    const unsub = useNavStore.subscribe(sync)
    return unsub
  }, [generatePlans])

  const selectedPlan = plans.find((p) => p.id === selectedPlanId)

  const handleStartBrowse = () => {
    const sequence = enterBrowse()
    if (sequence.length === 0) return
    initFromSequence(sequence)
    switchView('browse')
  }

  return (
    <div className={styles.view}>
      <div className={styles.topBar}>
        <button className={styles.back} onClick={() => switchView('nav')}>
          ← 返回导航
        </button>
        <h2 className={styles.title}>路线规划</h2>
      </div>

      {sourceWaypoints.length < 2 ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>至少需要 2 个途经点才能规划路线</p>
          <Button variant="outline" size="sm" onClick={() => switchView('nav')}>
            返回导航添加途经点
          </Button>
        </div>
      ) : (
        <>
          <WaypointModeToggle mode={waypointMode} onChange={setWaypointMode} />

          {/* 原始途经点参考区 */}
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>🧭 途经点 ({sourceWaypoints.length} 个)</h3>
            <div className={styles.wpList}>
              {sourceWaypoints.map((wp, i) => (
                <span key={`${wp.id}-${i}`} className={styles.wpItem}>
                  <span className={styles.wpIndex}>{i + 1}</span>
                  {wp.label}
                </span>
              ))}
            </div>
          </section>

          {/* 候选计划列表 */}
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>推荐路线</h3>
            {plans.length > 0 ? (
              <div className={styles.planList}>
                {plans.map((plan) => (
                  <PlanCard
                    key={plan.id}
                    plan={plan}
                    isSelected={plan.id === selectedPlanId}
                    onSelect={() => selectPlan(plan.id)}
                  />
                ))}
              </div>
            ) : (
              <p className={styles.empty}>途经点之间缺少直接连接路径</p>
            )}
          </section>

          {/* 底部操作 */}
          <div className={styles.bottomBar}>
            <Button variant="outline" size="sm" onClick={replan}>
              重新规划
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleStartBrowse}
              disabled={!selectedPlan}
            >
              开始浏览 ({selectedPlan?.sequence.length ?? 0} 站)
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

export default PlanView
