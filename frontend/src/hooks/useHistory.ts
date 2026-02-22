import { useCallback, useEffect, useState } from "react";
import {
  deleteHistoryEntry as apiDelete,
  fetchHistory,
  type HistoryEntry,
} from "../api";

export type { HistoryEntry } from "../api";

export function useHistory() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  const refresh = useCallback(async () => {
    const data = await fetchHistory();
    setEntries(data);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const removeEntry = useCallback(
    async (id: string) => {
      await apiDelete(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    },
    [],
  );

  return { entries, refresh, removeEntry };
}
