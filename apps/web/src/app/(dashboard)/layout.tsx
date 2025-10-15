import { DashboardShell } from '@/components/app/dashboard-shell';
import { SlipDrawer } from '@/components/app/slip-drawer';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardShell>
      {children}
      <SlipDrawer />
    </DashboardShell>
  );
}
