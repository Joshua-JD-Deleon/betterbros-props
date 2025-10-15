'use client';

import { ReactNode } from 'react';
import { Menu, TrendingUp, BarChart3, Settings, User } from 'lucide-react';
import { useUIStore } from '@/lib/store/ui-store';
import { useSlipStore } from '@/lib/store/slip-store';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { FilterPanel } from './filter-panel';

interface DashboardShellProps {
  children: ReactNode;
}

export function DashboardShell({ children }: DashboardShellProps) {
  const { isSidebarCollapsed, toggleSidebar, openDrawer } = useUIStore();
  const { entries } = useSlipStore();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Left Sidebar - Filters */}
      <aside
        className={cn(
          'border-r bg-card transition-all duration-300 ease-in-out',
          isSidebarCollapsed ? 'w-0' : 'w-[280px]'
        )}
      >
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center border-b px-4">
            <h2 className="text-lg font-semibold">Filters</h2>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
            <FilterPanel />
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navigation */}
        <header className="flex h-16 items-center justify-between border-b bg-card px-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
                <TrendingUp className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">BetterBros</span>
            </div>
          </div>

          <nav className="hidden items-center gap-6 md:flex">
            <a
              href="/"
              className="text-sm font-medium transition-colors hover:text-primary"
            >
              Dashboard
            </a>
            <a
              href="/analytics"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Analytics
            </a>
            <a
              href="/history"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              History
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              className="relative"
              onClick={openDrawer}
            >
              Slip
              {entries.length > 0 && (
                <span className="ml-2 flex h-5 w-5 items-center justify-center rounded-full bg-profit text-xs font-bold text-profit-foreground">
                  {entries.length}
                </span>
              )}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-full"
              aria-label="User menu"
            >
              <User className="h-5 w-5" />
            </Button>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto custom-scrollbar p-6">
          <div className="mx-auto max-w-[1400px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
