'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Trash2, TrendingUp } from 'lucide-react';
import { useUIStore } from '@/lib/store/ui-store';
import { useSlipStore } from '@/lib/store/slip-store';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { formatOdds, formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

export function SlipDrawer() {
  const { isDrawerOpen, closeDrawer } = useUIStore();
  const { entries, removeEntry, updateStake, clearSlip, getStats } = useSlipStore();
  const stats = getStats();

  return (
    <AnimatePresence>
      {isDrawerOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeDrawer}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 z-50 h-full w-full max-w-[400px] border-l bg-card shadow-2xl"
          >
            <div className="flex h-full flex-col">
              {/* Header */}
              <div className="flex items-center justify-between border-b p-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Bet Slip</h2>
                  {entries.length > 0 && (
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-profit text-xs font-bold text-profit-foreground">
                      {entries.length}
                    </span>
                  )}
                </div>
                <Button variant="ghost" size="icon" onClick={closeDrawer}>
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Entries */}
              <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
                {entries.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <div className="rounded-full bg-muted p-4">
                      <TrendingUp className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="mt-4 text-lg font-semibold">Empty Slip</h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Add props from the dashboard to build your slip
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {entries.map((entry) => (
                      <Card key={entry.id} className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="text-sm font-medium">
                              {entry.selection}
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">
                              {entry.market} · {entry.sportsbook}
                            </div>
                            <div className="mt-2 flex items-center gap-2">
                              <span className="odds-american text-sm">
                                {formatOdds(entry.odds)}
                              </span>
                              <span
                                className={cn(
                                  'text-xs font-semibold',
                                  entry.expectedValue > 0
                                    ? 'text-profit'
                                    : 'text-loss'
                                )}
                              >
                                {entry.expectedValue > 0 ? '+' : ''}
                                {entry.expectedValue.toFixed(2)}% EV
                              </span>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeEntry(entry.id)}
                            className="h-8 w-8"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>

                        <div className="mt-3">
                          <label className="text-xs text-muted-foreground">
                            Stake
                          </label>
                          <input
                            type="number"
                            min="0"
                            step="1"
                            value={entry.stake || ''}
                            onChange={(e) =>
                              updateStake(entry.id, Number(e.target.value))
                            }
                            className="mt-1 w-full rounded-md border bg-background px-3 py-2 text-sm"
                            placeholder="Enter stake..."
                          />
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>

              {/* Footer */}
              {entries.length > 0 && (
                <div className="border-t bg-background/50 p-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Stake</span>
                      <span className="font-medium">
                        {formatCurrency(stats.totalStake)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">
                        Potential Payout
                      </span>
                      <span className="font-medium">
                        {formatCurrency(stats.totalPotentialPayout)}
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-2">
                      <span className="text-muted-foreground">Total EV</span>
                      <span
                        className={cn(
                          'font-bold',
                          stats.totalExpectedValue > 0
                            ? 'text-profit'
                            : 'text-loss'
                        )}
                      >
                        {formatCurrency(stats.totalExpectedValue)}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={clearSlip}
                    >
                      Clear
                    </Button>
                    <Button className="flex-1" variant="profit">
                      Place Bets
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
