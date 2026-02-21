import { useCallback, useSyncExternalStore } from "react";

export interface HistoryEntry {
  id: string;
  text: string;
  jobSource: string;
  createdAt: string;
}

const STORAGE_KEY = "clg_history";
const MAX_ENTRIES = 30;

let listeners: Array<() => void> = [];

function emitChange() {
  for (const fn of listeners) fn();
}

function getSnapshot(): string {
  return localStorage.getItem(STORAGE_KEY) ?? "[]";
}

function subscribe(listener: () => void): () => void {
  listeners = [...listeners, listener];
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

function readEntries(): HistoryEntry[] {
  try {
    return JSON.parse(getSnapshot()) as HistoryEntry[];
  } catch {
    return [];
  }
}

function writeEntries(entries: HistoryEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  emitChange();
}

export function useHistory() {
  const raw = useSyncExternalStore(subscribe, getSnapshot);
  const entries: HistoryEntry[] = (() => {
    try {
      return JSON.parse(raw) as HistoryEntry[];
    } catch {
      return [];
    }
  })();

  const addEntry = useCallback((text: string, jobSource: string) => {
    const entry: HistoryEntry = {
      id: crypto.randomUUID(),
      text,
      jobSource,
      createdAt: new Date().toISOString(),
    };
    const updated = [entry, ...readEntries()].slice(0, MAX_ENTRIES);
    writeEntries(updated);
  }, []);

  const removeEntry = useCallback((id: string) => {
    writeEntries(readEntries().filter((e) => e.id !== id));
  }, []);

  const clearHistory = useCallback(() => {
    writeEntries([]);
  }, []);

  return { entries, addEntry, removeEntry, clearHistory };
}
