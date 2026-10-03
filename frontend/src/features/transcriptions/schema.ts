import { z } from "zod";

export const newTranscriptionSchema = z.object({
  file: z.instanceof(File, { message: "Pick a file or record something first." }),
  language: z.string(), // "" = auto-detect
  task: z.enum(["transcribe", "translate"]),
});

export type NewTranscriptionValues = z.infer<typeof newTranscriptionSchema>;
