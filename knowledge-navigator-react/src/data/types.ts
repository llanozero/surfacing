export interface CognitiveCard {
  id: string
  title: string
  type: 'folder' | 'leaf'
  tag?: string
  corpus: string[]
  description?: string
  bound_nodes?: string[]
  metadata?: {
    created_at?: string
    updated_at?: string
    generated?: boolean
  }
}

export interface NextNodeRef {
  target_id: string
  preset_weight: number
  browse_weight: number
  connection_type: 'preset' | 'browse_derived' | 'user_added'
}

export interface NavNode {
  id: string
  label: string
  description: string
  bound_cards?: string[]
  browse_history?: { from: string; count: number; last_at: string }[]
  next_nodes: NextNodeRef[]
  priority_config?: {
    mode: 'mixed' | 'user_only'
    preset_priority: number
    browse_priority: number
    user_overrides: { target_id: string; override_weight: number }[]
  }
}

export interface GraphEdge {
  source: string
  target: string
  weight: number
}

export interface BrowseCard {
  title: string
  desc: string
  tag: string
  weight: number
  cards: number
  corpus: string[]
  related: { name: string; pos: '前置' | '后置' }[]
}

export interface TreeNodeData {
  id: string
  title: string
  type: 'folder' | 'leaf'
  tag?: string
  children?: TreeNodeData[]
}
