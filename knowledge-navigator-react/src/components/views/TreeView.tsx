import React, { useRef, useState } from 'react'
import styles from './TreeView.module.css'
import SearchBar from '../shared/SearchBar'
import BreadcrumbNav from '../shared/BreadcrumbNav'
import TreeList from '../tree/TreeList'
import SubTabBar from '../tree/SubTabBar'
import CardEditPanel from '../tree/CardEditPanel'
import NodeManagementView from '../node-mgr/NodeManagementView'
import ImportConfirmDialog from '../dialog/ImportConfirmDialog'
import ImportErrorDialog from '../dialog/ImportErrorDialog'
import BackendSettingsDialog from '../settings/BackendSettingsDialog'
import { useTreeStore } from '../../store/treeStore'
import { useCardStore, getEditingCard } from '../../store/cardStore'
import { useNavNodeStore } from '../../store/navNodeStore'
import { useNavStore } from '../../store/navStore'
import { useToastStore } from '../shared/Toast'
import { getFullPath, getTreeNode, deriveParent } from '../../utils/treeUtils'
import {
  exportAllToYAML,
  downloadYAML,
  parseAndValidateYAML,
  computeImportPreview,
  mergeImportedData,
  type YamlData,
  type ImportPreview,
  type ValidationError,
} from '../../utils/yamlIO'

const TreeView: React.FC = () => {
  const { flatData, selectedId, searchQuery, setSearch, expandAncestors, selectNode } = useTreeStore()
  const allCards = useCardStore((s) => s.allCards)
  const createCard = useCardStore((s) => s.createCard)
  const { activeSubTab, setActiveSubTab } = useNavNodeStore()
  const toast = useToastStore((s) => s.show)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [pendingImport, setPendingImport] = useState<{ data: YamlData; preview: ImportPreview } | null>(null)
  const [importErrors, setImportErrors] = useState<ValidationError[] | null>(null)
  const [showBackendSettings, setShowBackendSettings] = useState(false)

  const breadcrumbs = selectedId ? getFullPath(flatData, selectedId) : []
  const editingCard = getEditingCard(allCards, selectedId)

  /**
   * 新建卡片：
   * - 选中文件夹 → 在其下创建子卡片
   * - 选中叶子卡片 → 创建同级兄弟卡片
   * - 未选中 → 创建一级卡片
   * 创建后自动展开父级并选中新卡片（编辑面板即时出现）
   */
  const handleAddCard = () => {
    const selected = selectedId ? getTreeNode(flatData, selectedId) : undefined
    let parentId: string | null = null
    if (selected) {
      parentId = selected.type === 'folder' ? selected.id : deriveParent(selected.id)
      if (parentId === 'root') parentId = null
    }
    const card = createCard(parentId)
    expandAncestors(card.id)
    selectNode(card.id)
    toast(`已创建卡片 ${card.id}`)
  }

  /** 导出：序列化当前全部卡片 + 节点为 YAML 并触发下载 */
  const handleExport = () => {
    const { allCards: cards } = useCardStore.getState()
    const { allNodes } = useNavNodeStore.getState()
    const yaml = exportAllToYAML(cards, allNodes)
    downloadYAML(yaml)
    toast(`已导出 ${cards.length} 张认知卡片和 ${allNodes.length} 个导航节点`)
  }

  /** 导入：读取文件 → 解析校验 → 确认对话框（失败则错误对话框） */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // 允许重复选择同一文件
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const result = parseAndValidateYAML(String(reader.result ?? ''))
      if (!result.ok) {
        setImportErrors(result.errors)
        return
      }
      const { allCards: cards } = useCardStore.getState()
      const { allNodes } = useNavNodeStore.getState()
      const preview = computeImportPreview(result.data, cards, allNodes)
      setPendingImport({ data: result.data, preview })
    }
    reader.onerror = () => toast('文件读取失败')
    reader.readAsText(file, 'utf-8')
  }

  /** 确认导入：upsert 合并到共享数据源并同步所有关联 Store */
  const handleConfirmImport = () => {
    if (!pendingImport) return
    const { data, preview } = pendingImport
    mergeImportedData(data, {
      onCardsMerged: (cards) => {
        useCardStore.setState({ allCards: [...cards] })
        // 同步树形视图扁平数据（title/type/tag 展示字段）
        useTreeStore.setState({
          flatData: cards.map((c) => ({ id: c.id, title: c.title, type: c.type, tag: c.tag })),
        })
      },
      onNodesMerged: (nodes) => {
        useNavNodeStore.setState({ allNodes: [...nodes] })
        // 同步导航画布（节点列表 + 边数据重算）
        useNavStore.getState().syncFromSource()
      },
    })
    setPendingImport(null)
    toast(`已导入 ${preview.cards.total} 张认知卡片和 ${preview.nodes.total} 个导航节点`)
  }

  return (
    <div className={styles.view}>
      <div className={styles.header}>
        <div className={styles.headerText}>
          <h1 className={styles.title}>
            {activeSubTab === 'cards' ? '认知卡片管理' : '导航节点管理'}
          </h1>
          <p className={styles.subtitle}>
            {activeSubTab === 'cards'
              ? `共 ${flatData.length} 张卡片 · 扁平存储，层级自动推导`
              : '编辑节点字段、绑定卡片与出向连接权重'}
          </p>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.ioBtn} onClick={() => fileInputRef.current?.click()}>
            导入
          </button>
          <button className={styles.ioBtn} onClick={handleExport}>
            导出
          </button>
          <button
            className={styles.ioBtn}
            onClick={() => setShowBackendSettings(true)}
            title="后端设置（本地 / 远程模式）"
            aria-label="后端设置"
          >
            ⚙
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
        </div>
      </div>

      <SubTabBar active={activeSubTab} onChange={setActiveSubTab} />

      {activeSubTab === 'cards' ? (
        <>
          <SearchBar
            placeholder="搜索认知卡片..."
            value={searchQuery}
            onChange={setSearch}
          />

          {breadcrumbs.length > 0 && (
            <BreadcrumbNav
              items={breadcrumbs}
              onSelect={(path) => {
                if (path !== 'root') expandAncestors(path)
              }}
            />
          )}

          <TreeList />

          {/* 选中卡片后的字段编辑面板（标题/描述/语料库/绑定节点） */}
          {editingCard && <CardEditPanel key={editingCard.id} card={editingCard} />}

          <button
            className={styles.fab}
            onClick={handleAddCard}
            aria-label="添加卡片"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </>
      ) : (
        <NodeManagementView />
      )}

      {/* YAML 导入：确认对话框 / 错误对话框（Portal 渲染） */}
      {pendingImport && (
        <ImportConfirmDialog
          preview={pendingImport.preview}
          onConfirm={handleConfirmImport}
          onCancel={() => setPendingImport(null)}
        />
      )}
      {importErrors && (
        <ImportErrorDialog errors={importErrors} onClose={() => setImportErrors(null)} />
      )}
      {showBackendSettings && (
        <BackendSettingsDialog onClose={() => setShowBackendSettings(false)} />
      )}
    </div>
  )
}

export default TreeView
