import { Card, CardDescription, CardTitle } from "ice-ds";

import { useServiceInfo } from "@/features/transcriptions/api";
import { NewTranscriptionForm } from "@/features/transcriptions/components/NewTranscriptionForm";
import { RecentList } from "@/features/transcriptions/components/RecentList";

export default function HomePage() {
  const { data: info } = useServiceInfo();
  const days = info ? Math.round(info.retention_hours / 24) : 3;

  return (
    <div className="space-y-10">
      <header className="space-y-4">
        <h1 className="text-5xl leading-[1.05] sm:text-6xl">
          Audio in.
          <br />
          <span className="bg-neo-pink px-2">Text out.</span>
        </h1>
        <p className="max-w-xl text-lg">
          Drop in a voice memo, interview, or meeting recording and get a transcript. No signup, no credit card,
          no trial that runs out.
        </p>
      </header>

      <NewTranscriptionForm />
      <RecentList />

      <section className="grid gap-4 sm:grid-cols-3">
        <Card variant="primary" elevation="sm">
          <CardTitle className="text-xl">No account</CardTitle>
          <CardDescription>You get a private link. That's it.</CardDescription>
        </Card>
        <Card variant="info" elevation="sm">
          <CardTitle className="text-xl">Audio deleted</CardTitle>
          <CardDescription>
            The file is wiped as soon as it's transcribed. Text self-destructs after {days} days.
          </CardDescription>
        </Card>
        <Card variant="premium" elevation="sm">
          <CardTitle className="text-xl">Open model</CardTitle>
          <CardDescription>
            Whisper runs on this server — nothing is sent to a third-party AI API.
          </CardDescription>
        </Card>
      </section>
    </div>
  );
}
