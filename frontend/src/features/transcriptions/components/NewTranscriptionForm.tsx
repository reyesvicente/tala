import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Button, Card, Field, Select, Tabs, TabsContent, TabsList, TabsTrigger } from "ice-ds";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { useCreateTranscription, useServiceInfo } from "../api";
import { newTranscriptionSchema, type NewTranscriptionValues } from "../schema";
import { useRecentStore } from "../store";
import { AudioPreview } from "./AudioPreview";
import { FileDrop } from "./FileDrop";
import { RecorderPanel } from "./RecorderPanel";

export function NewTranscriptionForm() {
  const navigate = useNavigate();
  const addRecent = useRecentStore((state) => state.add);
  const { data: info } = useServiceInfo();
  const createTranscription = useCreateTranscription();

  const {
    control,
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<NewTranscriptionValues>({
    resolver: zodResolver(newTranscriptionSchema),
    defaultValues: { language: "", task: "transcribe" },
  });

  const file = watch("file");
  const setFile = (next: File) => setValue("file", next, { shouldValidate: true });
  const tooLarge = !!(info && file && file.size > info.max_upload_mb * 1024 * 1024);

  const onSubmit = handleSubmit((values) => {
    if (tooLarge) return;
    createTranscription.mutate(values, {
      onSuccess: (job) => {
        // Account uploads live in "My transcripts"; keep their names out of this shared browser list.
        if (!job.private)
          addRecent({
          slug: job.slug,
          filename: job.original_filename,
          createdAt: job.created_at,
          expiresAt: job.expires_at,
        });
        navigate(`/t/${job.slug}`);
      },
    });
  });

  return (
    <Card elevation="lg" className="space-y-6 bg-white">
      <form onSubmit={onSubmit} className="space-y-6" noValidate>
        <Tabs defaultValue="upload">
          <TabsList variant="boxed" className="mb-4">
            <TabsTrigger value="upload" variant="boxed">
              Upload a file
            </TabsTrigger>
            <TabsTrigger value="record" variant="boxed">
              Record now
            </TabsTrigger>
          </TabsList>
          <TabsContent value="upload">
            <FileDrop file={file ?? null} onFile={setFile} maxMb={info?.max_upload_mb} />
          </TabsContent>
          <TabsContent value="record">
            <RecorderPanel file={file ?? null} onRecorded={setFile} />
          </TabsContent>
        </Tabs>

        {file && <AudioPreview file={file} />}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Spoken language" htmlFor="language" hint="Auto-detect works for ~100 languages.">
            <Select id="language" {...register("language")}>
              <option value="">Auto-detect</option>
              {Object.entries(info?.languages ?? {}).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Output" htmlFor="task" hint="Translate turns any language into English text.">
            <Controller
              control={control}
              name="task"
              render={({ field }) => (
                <Select id="task" {...field}>
                  <option value="transcribe">Transcript in the same language</option>
                  <option value="translate">Translate to English</option>
                </Select>
              )}
            />
          </Field>
        </div>

        {errors.file && <Alert intent="error" title={errors.file.message} />}
        {tooLarge && <Alert intent="error" title={`That file is over the ${info?.max_upload_mb} MB limit.`} />}
        {createTranscription.isError && <Alert intent="error" title={createTranscription.error.message} />}

        <Button type="submit" size="xl" fullWidth loading={createTranscription.isPending} disabled={tooLarge}>
          {createTranscription.isPending ? "Uploading…" : "Turn it into text"}
        </Button>
      </form>
    </Card>
  );
}
