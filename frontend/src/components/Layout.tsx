import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Brain, LayoutDashboard, FileText, BarChart3, Settings, Menu, X, ChevronLeft } from 'lucide-react'
import { cn } from '../utils/helpers'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'New Analysis', href: '/analyze', icon: FileText },
  { name: 'Subjects', href: '/subjects', icon: Brain },
  { name: 'Model', href: '/model', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-neuro-50 flex">
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-neuro-200 transform transition-transform duration-300 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-6 border-b border-neuro-200">
            <Link to="/" className="flex items-center gap-2">
              <Brain className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold text-neuro-900">NeuroTrace</span>
            </Link>
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-neuro-100"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href))
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-neuro-600 hover:bg-neuro-100 hover:text-neuro-900'
                  )}
                >
                  <item.icon className="w-5 h-5" aria-hidden="true" />
                  {item.name}
                </Link>
              )
            })}
          </nav>
          <div className="p-4 border-t border-neuro-200">
            <div className="text-xs text-neuro-500">
              v1.0.0 | Research Use Only
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 lg:pl-0">
        <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-sm border-b border-neuro-200">
          <div className="flex items-center justify-between h-16 px-4 lg:px-8">
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-neuro-100"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex-1 lg:flex-none" />
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 text-sm text-neuro-500">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span>Backend Connected</span>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8 overflow-auto">
          <Outlet />
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  )
}

import { useState } from 'react'