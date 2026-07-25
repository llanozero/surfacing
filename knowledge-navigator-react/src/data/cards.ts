import type { CognitiveCard } from './types'

/**
 * 认知卡片扁平数据（对应 data-model.md 中的 YAML 扁平存储结构）
 * parent / children 不存储，由 treeUtils 根据 id 层级路径推导。
 */
export const cognitiveCards: CognitiveCard[] = [
  {
    id: 'root/1',
    title: '机器学习',
    type: 'folder',
    tag: '层级分类',
    description: '人工智能的子领域，使计算机能够从数据中学习和改进。',
    corpus: [
      '机器学习是人工智能的一个子领域，使计算机能够从数据中学习和改进。',
      '主要范式包括监督学习、无监督学习和强化学习。',
    ],
    bound_nodes: ['node-ml-foundation', 'node-ai-intro'],
  },
  {
    id: 'root/1/1',
    title: '监督学习',
    type: 'leaf',
    tag: '决策分支',
    description: '使用标注数据训练模型，学习输入到输出的映射函数。',
    corpus: [
      '使用标注数据训练模型，学习从输入到输出的映射函数。',
      '常见算法包括线性回归、逻辑回归、SVM、决策树和神经网络。',
    ],
    bound_nodes: ['node-supervised', 'node-ml-foundation'],
  },
  {
    id: 'root/1/2',
    title: '无监督学习',
    type: 'leaf',
    tag: '层级分类',
    description: '从未标注数据中发现隐藏的模式和结构。',
    corpus: [
      '从未标注数据中发现隐藏的模式和结构。',
      '常见算法包括聚类（K-means）、降维（PCA）和关联规则学习。',
    ],
    bound_nodes: ['node-unsupervised'],
  },
  {
    id: 'root/1/3',
    title: '强化学习',
    type: 'leaf',
    tag: '决策分支',
    description: '智能体通过与环境交互、基于奖励信号学习最优策略。',
    corpus: [
      '强化学习关注智能体如何在环境中采取行动以最大化累积奖励。',
      '核心概念包括状态、动作、奖励、策略与价值函数，代表算法有 Q-Learning 与策略梯度。',
    ],
    bound_nodes: ['node-reinforcement'],
  },
  {
    id: 'root/2',
    title: '神经网络',
    type: 'folder',
    tag: '层级分类',
    description: '受生物神经网络启发设计的计算模型。',
    corpus: [
      '受生物神经网络启发设计的计算模型，由大量相互连接的神经元层构成。',
      '通过反向传播算法调整权重，拟合复杂的非线性映射。',
    ],
    bound_nodes: ['node-nn-foundation'],
  },
  {
    id: 'root/2/1',
    title: 'CNN 卷积神经网络',
    type: 'leaf',
    tag: '决策分支',
    description: '利用卷积核提取局部特征，是计算机视觉的基石。',
    corpus: [
      '卷积神经网络通过卷积层、池化层堆叠提取图像的层次化特征。',
      '代表结构：LeNet、AlexNet、ResNet。',
    ],
    bound_nodes: ['node-cnn', 'node-cv'],
  },
  {
    id: 'root/2/2',
    title: 'RNN 循环神经网络',
    type: 'leaf',
    tag: '层级分类',
    description: '具有时序记忆能力，适用于序列建模。',
    corpus: [
      '循环神经网络通过隐状态传递历史信息，适用于文本、语音等序列数据。',
      'LSTM 与 GRU 通过门控机制缓解长序列梯度消失问题。',
    ],
    bound_nodes: ['node-rnn', 'node-nlp'],
  },
  {
    id: 'root/2/3',
    title: '注意力机制',
    type: 'leaf',
    tag: '决策分支',
    description: '让模型动态聚焦输入中最相关的部分。',
    corpus: [
      '注意力机制通过查询、键、值计算相关性权重，实现对输入的软选择。',
      '自注意力是 Transformer 的核心构件。',
    ],
    bound_nodes: ['node-attention', 'node-nlp'],
  },
  {
    id: 'root/3',
    title: '深度学习',
    type: 'folder',
    tag: '层级分类',
    description: '基于多层神经网络的机器学习方法。',
    corpus: [
      '深度学习使用多层神经网络逐层抽象数据特征。',
      '训练依赖大规模数据、GPU 算力与反向传播算法。',
    ],
    bound_nodes: ['node-deep-learning'],
  },
  {
    id: 'root/3/1',
    title: '反向传播',
    type: 'leaf',
    tag: '层级分类',
    description: '通过链式法则高效计算梯度并更新网络权重。',
    corpus: [
      '反向传播利用链式法则从输出层向输入层逐层传递误差梯度。',
      '配合梯度下降及其变体（SGD、Adam）完成参数优化。',
    ],
    bound_nodes: ['node-deep-learning'],
  },
  {
    id: 'root/4',
    title: '自然语言处理',
    type: 'folder',
    tag: '层级分类',
    description: '让计算机理解、生成和处理人类语言。',
    corpus: [
      '自然语言处理涵盖分词、词性标注、命名实体识别、机器翻译等任务。',
      '现代 NLP 以预训练语言模型为主导范式。',
    ],
    bound_nodes: ['node-nlp'],
  },
  {
    id: 'root/4/1',
    title: '词嵌入',
    type: 'leaf',
    tag: '决策分支',
    description: '将词语映射为稠密向量，捕捉语义关系。',
    corpus: [
      '词嵌入将离散词语映射到低维稠密向量空间。',
      'Word2Vec、GloVe 是经典的静态词嵌入方法。',
    ],
    bound_nodes: ['node-word-embedding', 'node-nlp'],
  },
  {
    id: 'root/4/2',
    title: 'Transformer',
    type: 'leaf',
    tag: '决策分支',
    description: '完全基于注意力机制的序列建模架构。',
    corpus: [
      'Transformer 摒弃循环结构，完全依赖自注意力机制并行处理序列。',
      'BERT、GPT 等大模型均构建于 Transformer 之上。',
    ],
    bound_nodes: ['node-transformer', 'node-attention'],
  },
  {
    id: 'root/5',
    title: '计算机视觉',
    type: 'folder',
    tag: '层级分类',
    description: '让计算机从图像和视频中获取理解。',
    corpus: [
      '计算机视觉涵盖图像分类、目标检测、语义分割与图像生成。',
      '卷积神经网络与视觉 Transformer 是两大主流架构。',
    ],
    bound_nodes: ['node-cv'],
  },
  {
    id: 'root/5/1',
    title: '目标检测',
    type: 'leaf',
    tag: '决策分支',
    description: '在图像中定位并识别多个目标。',
    corpus: [
      '目标检测同时输出目标的类别与边界框位置。',
      '代表算法：YOLO、Faster R-CNN、DETR。',
    ],
    bound_nodes: ['node-cv', 'node-cnn'],
  },
  {
    id: 'root/6',
    title: '数学基础',
    type: 'folder',
    tag: '层级分类',
    description: '机器学习所需的数学工具集合。',
    corpus: [
      '概率论、线性代数与微积分是理解机器学习算法的三大数学支柱。',
    ],
    bound_nodes: ['node-math-foundation'],
  },
  {
    id: 'root/6/1',
    title: '概率论',
    type: 'leaf',
    tag: '层级分类',
    description: '研究随机现象规律，是统计学习的语言。',
    corpus: [
      '概率论为不确定性建模提供形式化工具。',
      '贝叶斯定理、期望、方差与常见分布是机器学习的必备基础。',
    ],
    bound_nodes: ['node-probability', 'node-math-foundation'],
  },
  {
    id: 'root/6/2',
    title: '线性代数',
    type: 'leaf',
    tag: '层级分类',
    description: '向量、矩阵与张量运算是深度学习的计算骨架。',
    corpus: [
      '线性代数研究向量空间与线性映射。',
      '矩阵分解、特征值与奇异值分解广泛应用于降维与推荐系统。',
    ],
    bound_nodes: ['node-linear-algebra', 'node-math-foundation'],
  },
]

export function getCard(id: string): CognitiveCard | undefined {
  return cognitiveCards.find((c) => c.id === id)
}
