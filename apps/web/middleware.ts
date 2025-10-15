import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Authentication Middleware with Environment-Based Provider Switching
 *
 * Supports both Clerk and Supabase authentication based on AUTH_PROVIDER env var.
 * Protects dashboard and API routes while allowing public access to auth pages.
 */

// Define public routes that don't require authentication
const publicRoutes = [
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/public(.*)',
  '/api/webhooks(.*)',
  '/about',
  '/pricing',
  '/contact',
];

// Define protected routes that require authentication
const protectedRoutes = [
  '/dashboard(.*)',
  '/props(.*)',
  '/optimize(.*)',
  '/experiments(.*)',
  '/api/props(.*)',
  '/api/optimize(.*)',
  '/api/experiments(.*)',
];

// Get auth provider from environment
const AUTH_PROVIDER = process.env.NEXT_PUBLIC_AUTH_PROVIDER || process.env.AUTH_PROVIDER || 'clerk';

/**
 * Clerk-based middleware
 */
const isPublicRoute = createRouteMatcher(publicRoutes);

const clerkAuthMiddleware = clerkMiddleware((auth, request) => {
  // Protect non-public routes
  if (!isPublicRoute(request)) {
    auth().protect();
  }
});

/**
 * Supabase-based middleware
 */
async function supabaseAuthMiddleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if route is public
  const isPublic = publicRoutes.some((route) => {
    const pattern = route.replace('(.*)', '.*');
    return new RegExp(`^${pattern}$`).test(pathname);
  });

  // Allow public routes
  if (isPublic) {
    return NextResponse.next();
  }

  // Check for authentication token in cookies
  const token = request.cookies.get('sb-access-token')?.value;

  // If no token and route is protected, redirect to sign-in
  if (!token) {
    const isProtected = protectedRoutes.some((route) => {
      const pattern = route.replace('(.*)', '.*');
      return new RegExp(`^${pattern}$`).test(pathname);
    });

    if (isProtected) {
      const signInUrl = new URL('/sign-in', request.url);
      signInUrl.searchParams.set('redirect', pathname);
      return NextResponse.redirect(signInUrl);
    }
  }

  return NextResponse.next();
}

/**
 * Main middleware that switches based on AUTH_PROVIDER
 */
export default async function middleware(request: NextRequest) {
  // Use Clerk middleware if AUTH_PROVIDER is 'clerk' (default)
  if (AUTH_PROVIDER === 'clerk') {
    return clerkAuthMiddleware(request);
  }

  // Use Supabase middleware if AUTH_PROVIDER is 'supabase'
  if (AUTH_PROVIDER === 'supabase') {
    return supabaseAuthMiddleware(request);
  }

  // Fallback: no authentication (development only)
  console.warn(`Unknown AUTH_PROVIDER: ${AUTH_PROVIDER}, allowing all requests`);
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
