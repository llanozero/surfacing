import type { GraphEdge, NavNode } from './types'

/**
 * 全部导航节点（对应 data-model.md 中的 navigation_nodes）。
 * next_nodes 定义出向连接及双重权重（预设 + 浏览行为）。
 */
export const allNavNodes: NavNode[] = [
  {
    id: 'node-ai-intro',
    label: 'AI 入门',
    description: '人工智能概览，建立对机器学习、神经网络与应用版图的整体认知。',
    bound_cards: ['root/1'],
    next_nodes: [
      { target_id: 'node-math-foundation', preset_weight: 0.7, browse_weight: 0.5, connection_type: 'preset' },
      { target_id: 'node-ml-foundation', preset_weight: 0.85, browse_weight: 0.62, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-math-foundation',
    label: '数学基础',
    description: '概率论、线性代数与微积分——机器学习算法的数学语言。',
    bound_cards: ['root/6'],
    next_nodes: [
      { target_id: 'node-probability', preset_weight: 0.78, browse_weight: 0.55, connection_type: 'preset' },
      { target_id: 'node-linear-algebra', preset_weight: 0.82, browse_weight: 0.48, connection_type: 'preset' },
      { target_id: 'node-ml-foundation', preset_weight: 0.5, browse_weight: 0.6, connection_type: 'browse_derived' },
    ],
  },
  {
    id: 'node-probability',
    label: '概率论',
    description: '随机变量、概率分布与贝叶斯推断。',
    bound_cards: ['root/6/1'],
    next_nodes: [
      { target_id: 'node-ml-foundation', preset_weight: 0.75, browse_weight: 0.42, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-linear-algebra',
    label: '线性代数',
    description: '向量空间、矩阵运算与特征分解。',
    bound_cards: ['root/6/2'],
    next_nodes: [
      { target_id: 'node-ml-foundation', preset_weight: 0.8, browse_weight: 0.5, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-ml-foundation',
    label: '机器学习基础',
    description: '涵盖监督学习、无监督学习与强化学习的核心概念与算法基础。',
    bound_cards: ['root/1', 'root/1/1'],
    browse_history: [
      { from: 'node-probability', count: 3, last_at: '2026-07-24T09:30:00Z' },
      { from: 'node-linear-algebra', count: 5, last_at: '2026-07-24T08:15:00Z' },
    ],
    next_nodes: [
      { target_id: 'node-supervised', preset_weight: 0.75, browse_weight: 0.42, connection_type: 'preset' },
      { target_id: 'node-unsupervised', preset_weight: 0.6, browse_weight: 0.3, connection_type: 'preset' },
      { target_id: 'node-reinforcement', preset_weight: 0.4, browse_weight: 0.25, connection_type: 'preset' },
      { target_id: 'node-nn-foundation', preset_weight: 0.55, browse_weight: 0.58, connection_type: 'browse_derived' },
    ],
    priority_config: { mode: 'mixed', preset_priority: 0, browse_priority: 4, user_overrides: [] },
  },
  {
    id: 'node-supervised',
    label: '监督学习',
    description: '回归与分类：从标注数据学习映射函数。',
    bound_cards: ['root/1/1'],
    next_nodes: [
      { target_id: 'node-nn-foundation', preset_weight: 0.7, browse_weight: 0.52, connection_type: 'preset' },
      { target_id: 'node-deep-learning', preset_weight: 0.45, browse_weight: 0.4, connection_type: 'browse_derived' },
    ],
  },
  {
    id: 'node-unsupervised',
    label: '无监督学习',
    description: '聚类、降维与关联规则——发现数据的内在结构。',
    bound_cards: ['root/1/2'],
    next_nodes: [
      { target_id: 'node-deep-learning', preset_weight: 0.5, browse_weight: 0.35, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-reinforcement',
    label: '强化学习',
    description: '基于奖励信号的策略优化，从 Q-Learning 到 PPO。',
    bound_cards: ['root/1/3'],
    next_nodes: [
      { target_id: 'node-deep-learning', preset_weight: 0.55, browse_weight: 0.3, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-nn-foundation',
    label: '神经网络基础',
    description: '神经元、激活函数与前馈网络结构。',
    bound_cards: ['root/2'],
    next_nodes: [
      { target_id: 'node-deep-learning', preset_weight: 0.8, browse_weight: 0.6, connection_type: 'preset' },
      { target_id: 'node-cnn', preset_weight: 0.6, browse_weight: 0.45, connection_type: 'preset' },
      { target_id: 'node-rnn', preset_weight: 0.55, browse_weight: 0.4, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-deep-learning',
    label: '深度学习',
    description: '多层网络训练：反向传播、优化器与正则化。',
    bound_cards: ['root/3', 'root/3/1'],
    next_nodes: [
      { target_id: 'node-cnn', preset_weight: 0.65, browse_weight: 0.5, connection_type: 'preset' },
      { target_id: 'node-attention', preset_weight: 0.7, browse_weight: 0.62, connection_type: 'preset' },
      { target_id: 'node-nlp', preset_weight: 0.5, browse_weight: 0.55, connection_type: 'browse_derived' },
      { target_id: 'node-cv', preset_weight: 0.5, browse_weight: 0.44, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-cnn',
    label: '卷积神经网络',
    description: '卷积、池化与残差连接，视觉任务的核心架构。',
    bound_cards: ['root/2/1'],
    next_nodes: [
      { target_id: 'node-cv', preset_weight: 0.75, browse_weight: 0.55, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-rnn',
    label: '循环神经网络',
    description: '序列建模与门控机制（LSTM / GRU）。',
    bound_cards: ['root/2/2'],
    next_nodes: [
      { target_id: 'node-attention', preset_weight: 0.6, browse_weight: 0.5, connection_type: 'preset' },
      { target_id: 'node-nlp', preset_weight: 0.55, browse_weight: 0.4, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-attention',
    label: '注意力机制',
    description: 'Query-Key-Value 与自注意力计算。',
    bound_cards: ['root/2/3', 'root/4/2'],
    next_nodes: [
      { target_id: 'node-transformer', preset_weight: 0.85, browse_weight: 0.7, connection_type: 'preset' },
    ],
  },
  {
    id: 'node-transformer',
    label: 'Transformer',
    description: '多头注意力与前馈层堆叠的现代架构。',
    bound_cards: ['root/4/2'],
    next_nodes: [
      { target_id: 'node-nlp', preset_weight: 0.8, browse_weight: 0.66, connection_type: 'preset' },
      { target_id: 'node-cv', preset_weight: 0.4, browse_weight: 0.35, connection_type: 'browse_derived' },
    ],
  },
  {
    id: 'node-nlp',
    label: 'NLP 专项',
    description: '从词嵌入到预训练语言模型的完整路径。',
    bound_cards: ['root/4'],
    next_nodes: [
      { target_id: 'node-word-embedding', preset_weight: 0.65, browse_weight: 0.4, connection_type: 'preset' },
      { target_id: 'node-transformer', preset_weight: 0.6, browse_weight: 0.5, connection_type: 'user_added' },
    ],
  },
  {
    id: 'node-word-embedding',
    label: '词嵌入',
    description: 'Word2Vec / GloVe：词语的向量化表示。',
    bound_cards: ['root/4/1'],
    next_nodes: [
      { target_id: 'node-rnn', preset_weight: 0.55, browse_weight: 0.42, connection_type: 'preset' },
      { target_id: 'node-attention', preset_weight: 0.5, browse_weight: 0.55, connection_type: 'browse_derived' },
    ],
  },
  {
    id: 'node-cv',
    label: 'CV 专项',
    description: '图像分类、目标检测与视觉生成。',
    bound_cards: ['root/5', 'root/5/1'],
    next_nodes: [
      { target_id: 'node-cnn', preset_weight: 0.6, browse_weight: 0.45, connection_type: 'preset' },
    ],
  },
]

export const navNodeMap: Map<string, NavNode> = new Map(allNavNodes.map((n) => [n.id, n]))

export function getNavNode(id: string): NavNode | undefined {
  return navNodeMap.get(id)
}

/** 由 next_nodes 推导全量有向边（力导向图用） */
export const allEdges: GraphEdge[] = allNavNodes.flatMap((n) =>
  n.next_nodes.map((e) => ({
    source: n.id,
    target: e.target_id,
    weight: e.preset_weight,
  })),
)
