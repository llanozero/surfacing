import { useCallback, useEffect, useRef, useState } from 'react'
import type { CognitiveCard, NavNode } from '../data/types'
import {
  aiCardTitle,
  aiCardDescription,
  aiNodeLabel,
  aiNodeDescription,
  type AiResult,
} from '../utils/aiGenerateCore'

/**
 * AI 辅助字段生成 Hook（React 封装层）。
 * 核心逻辑在 utils/aiGenerateCore.ts（浏览器与 Node/CLI 通用），
 * 本 Hook 只负责 generating 状态与组件卸载时的请求取消。
 */

export type { AiResult }

export function useAiGenerate() {
  const [generating, setGenerating] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  // 卸载（如切换编辑对象导致面板重挂载）时取消未完成的请求
  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  /** 包装核心调用：管理 generating 状态 + 新建 AbortController */
  const run = useCallback(
    async (
      task: (signal: AbortSignal) => Promise<AiResult | null>,
    ): Promise<AiResult | null> => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      setGenerating(true)
      try {
        // 注意：核心内部以 30s 超时兜底；这里传入 signal 仅用于卸载取消，
        // 但核心 generateField 的外部 signal 取消不降级 —— 需要保留降级语义时传 undefined。
        // 面板场景下卸载即放弃结果，符合预期。
        return await task(controller.signal)
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null
          setGenerating(false)
        }
      }
    },
    [],
  )

  const generateCardTitle = useCallback(
    (card: CognitiveCard, children: CognitiveCard[]) =>
      run(() => aiCardTitle(card, children)),
    [run],
  )

  const generateCardDescription = useCallback(
    (card: CognitiveCard, children: CognitiveCard[]) =>
      run(() => aiCardDescription(card, children)),
    [run],
  )

  const generateNodeLabel = useCallback(
    (node: NavNode, boundCards: CognitiveCard[]) =>
      run(() => aiNodeLabel(node, boundCards)),
    [run],
  )

  const generateNodeDescription = useCallback(
    (node: NavNode, boundCards: CognitiveCard[], prevNodes: NavNode[], nextNodes: NavNode[]) =>
      run(() => aiNodeDescription(node, boundCards, prevNodes, nextNodes)),
    [run],
  )

  return { generating, generateCardTitle, generateCardDescription, generateNodeLabel, generateNodeDescription }
}
