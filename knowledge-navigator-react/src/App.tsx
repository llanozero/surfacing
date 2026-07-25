import { useEffect } from 'react'
import { useViewStore, type ViewName } from './store/viewStore'
import { useBrowseStore } from './store/browseStore'
import StatusBar from './components/layout/StatusBar'
import TabBar from './components/layout/TabBar'
import SearchView from './components/views/SearchView'
import NavView from './components/views/NavView'
import PlanView from './components/plan/PlanView'
import BrowseView from './components/views/BrowseView'
import TreeView from './components/views/TreeView'
import Toast from './components/shared/Toast'

const viewMap: Record<ViewName, React.FC> = {
  search: SearchView,
  nav: NavView,
  plan: PlanView,
  browse: BrowseView,
  tree: TreeView,
}

function App() {
  const activeView = useViewStore((s) => s.activeView)
  const CurrentView = viewMap[activeView]

  // 键盘快捷键：1-5 切换视图；浏览视图中 ↑↓ 切换卡片
  useEffect(() => {
    const keys: Record<string, ViewName> = {
      '1': 'search', '2': 'nav', '3': 'plan', '4': 'browse', '5': 'tree',
    }
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return
      const view = keys[e.key]
      if (view) {
        useViewStore.getState().switchView(view)
        return
      }
      if (useViewStore.getState().activeView === 'browse') {
        if (e.key === 'ArrowDown') useBrowseStore.getState().nextCard()
        else if (e.key === 'ArrowUp') useBrowseStore.getState().prevCard()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <div id="app">
      <StatusBar />
      <main className="view-container">
        <CurrentView />
      </main>
      <TabBar />
      <Toast />
    </div>
  )
}

export default App
