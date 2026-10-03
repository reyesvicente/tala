import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export interface RecentItem {
  slug: string;
  filename: string;
  createdAt: string;
  expiresAt: string;
}

interface RecentState {
  items: RecentItem[];
  add: (item: RecentItem) => void;
  remove: (slug: string) => void;
}

// For logged-out users, "your transcripts" is just the links this browser has made.
export const useRecentStore = create<RecentState>()(
  persist(
    (set) => ({
      items: [],
      add: (item) =>
        set((state) => ({ items: [item, ...state.items.filter((i) => i.slug !== item.slug)].slice(0, 20) })),
      remove: (slug) => set((state) => ({ items: state.items.filter((i) => i.slug !== slug) })),
    }),
    {
      name: "tala-recent",
      storage: createJSONStorage(() => localStorage),
      merge: (persisted, current) => {
        const items = ((persisted as Partial<RecentState>)?.items ?? []).filter(
          (i) => new Date(i.expiresAt).getTime() > Date.now(),
        );
        return { ...current, items };
      },
    },
  ),
);
