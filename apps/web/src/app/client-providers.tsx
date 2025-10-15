'use client';

import { ThemeProvider } from 'next-themes';
import { Providers } from './providers';
import type { ReactNode } from 'react';

export function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
    >
      <Providers>{children}</Providers>
    </ThemeProvider>
  );
}
