import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto w-full max-w-5xl px-6 py-14">
        <h1 className="text-3xl font-semibold tracking-tight">AInfluencer</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          MVP goal: a clean dashboard that installs dependencies, runs checks, logs everything, and
          makes the system usable on Windows + macOS.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          <Link
            href="/installer"
            className="rounded-xl border border-zinc-200 bg-white p-5 hover:bg-zinc-50"
          >
            <div className="text-sm font-semibold">Setup / Installer</div>
            <div className="mt-2 text-sm text-zinc-600">
              One click → check system → install → test → view logs.
            </div>
          </Link>

          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <div className="text-sm font-semibold">Next (coming)</div>
            <div className="mt-2 text-sm text-zinc-600">
              Model Manager → Image Generation → Content Library.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
