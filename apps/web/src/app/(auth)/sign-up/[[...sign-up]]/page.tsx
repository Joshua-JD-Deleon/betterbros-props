import { SignUp } from '@clerk/nextjs';

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md space-y-8 px-4">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">BetterBros</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Create an account to start trading props
          </p>
        </div>

        <SignUp
          appearance={{
            elements: {
              rootBox: 'mx-auto',
              card: 'bg-card shadow-xl',
            },
          }}
        />
      </div>
    </div>
  );
}
