import Link from "next/link";
import { LogoLockup } from "@/components/brand/logo-lockup";
import { WaveformMotif } from "@/components/brand/waveform-motif";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-background">
      <div className="relative w-full max-w-2xl text-center space-y-8">
        {/* Decorative abstract waveform — NOT a real patient trace */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 opacity-30 pointer-events-none" aria-hidden="true">
          <WaveformMotif />
        </div>

        <div className="relative space-y-6">
          {/* Logo lockup */}
          <div className="flex justify-center">
            <LogoLockup />
          </div>

          {/* Benefit-led hero copy — from branding/03 */}
          <div className="space-y-3">
            <h1 className="text-4xl font-bold tracking-tight text-foreground">
              Know which signals you can trust — in minutes, with the evidence behind every call.
            </h1>
            <p className="text-lg text-muted-foreground">
              Agentic ECG and PPG quality assessment for clinical research.
            </p>
          </div>

          {/* Single primary indigo CTA */}
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button asChild size="lg">
              <Link href="/dashboard">Open Dashboard</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
                target="_blank"
                rel="noopener noreferrer"
              >
                API Docs
              </a>
            </Button>
          </div>
        </div>
      </div>
    </main>
  );
}
