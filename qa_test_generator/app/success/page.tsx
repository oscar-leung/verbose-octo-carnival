import Link from "next/link";

export const dynamic = "force-dynamic";

export default function SuccessPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-20 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">You&apos;re subscribed.</h1>
      <p className="mt-3 text-neutral-600 dark:text-neutral-400">
        Your subscription is active. Your plan will show as unlimited within a few seconds,
        once Stripe confirms with our server. If it doesn&apos;t, refresh the page.
      </p>
      <Link
        href="/"
        className="mt-8 inline-block rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white dark:bg-neutral-100 dark:text-neutral-900"
      >
        Back to generator
      </Link>
    </main>
  );
}
