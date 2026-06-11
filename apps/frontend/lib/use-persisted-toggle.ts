"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * A boolean display preference persisted in `localStorage` (J-44 index-card toggle + J-45 regime-band
 * toggle). It is a pure CLIENT display preference — it never changes any served value, only whether a
 * surface is shown.
 *
 * SSR-safe: it initializes to `defaultValue` on the server / first client render (so markup is stable),
 * then hydrates the stored value in an effect — avoiding a hydration mismatch. A fresh browser (no stored
 * key) therefore defaults to `defaultValue` (ON for both toggles), and once the user flips it the choice
 * survives reloads. A malformed / unavailable `localStorage` degrades to `defaultValue` (never crashes).
 */
export function usePersistedToggle(
  storageKey: string,
  defaultValue: boolean,
): [boolean, (next: boolean) => void] {
  const [value, setValue] = useState<boolean>(defaultValue);

  // Hydrate from localStorage once, after mount (SSR-safe — server render used `defaultValue`).
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw === "true") setValue(true);
      else if (raw === "false") setValue(false);
    } catch {
      /* localStorage unavailable (private mode / blocked) — keep the default */
    }
  }, [storageKey]);

  const set = useCallback(
    (next: boolean) => {
      setValue(next);
      try {
        window.localStorage.setItem(storageKey, next ? "true" : "false");
      } catch {
        /* best-effort persistence — the in-memory value still updates */
      }
    },
    [storageKey],
  );

  return [value, set];
}
