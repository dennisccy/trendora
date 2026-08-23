import type { badgeVariants } from "@/components/ui/badge";
import type { VariantProps } from "class-variance-authority";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

/** Mirrors the backend's `CompassBasisDisclosure.status` string-literal union (lib/api.ts) -- kept as
 *  its own local type here (rather than importing from api.ts) so this pure module stays
 *  dependency-free and runnable under plain `node lib/basis-disclosure-label.test.ts` (the project
 *  convention, no test framework installed) without pulling in api.ts's fetch machinery. */
export type CompassBasisStatus = "available" | "unavailable" | "rebuilt" | "unverifiable";

export interface BasisDisclosureLabel {
  variant: BadgeVariant;
  label: string;
}

/**
 * goal-market-compass iter-11 -- the single status -> {variant, label} mapping for the manifest strip's
 * basis-disclosure badge (`compass-manifest-strip.tsx`'s `BasisLine`), extracted from its previously
 * inline ternary -- a mechanical refactor, no behavior change for the three pre-existing statuses.
 *
 * The fourth status, `"unverifiable"`, is new this iteration (backend fail-closed fix,
 * `app.engine.compass.basis_disclosure`, docs/goal.md J-11 step 11 ruling A4): it reports an HONEST
 * "no basis was ever recorded, or it could not be read" fact -- never a confident claim (AG-1: "never a
 * confident claim"). It must read visibly distinct from BOTH:
 *   - `"available"` (`ok` / green)      -- a confident "the original basis is intact" claim;
 *   - `"unavailable"` (`danger` / red)  -- a DIFFERENT fact: the source run IS gone, not merely
 *     unrecorded/unreadable.
 * So it gets the neutral `default` badge variant -- never `ok`, `warn`, or `danger` -- and its own
 * distinct label, never collapsed into either neighbor's wording.
 */
export function basisDisclosureLabel(status: CompassBasisStatus): BasisDisclosureLabel {
  switch (status) {
    case "available":
      return { variant: "ok", label: "Basis: available" };
    case "rebuilt":
      return { variant: "warn", label: "Basis: rebuilt" };
    case "unavailable":
      return { variant: "danger", label: "Basis: unavailable" };
    case "unverifiable":
      return { variant: "default", label: "Basis: unverifiable" };
    default: {
      // exhaustiveness guard -- a future status literal must be handled explicitly above; never
      // silently fall through to a variant that could be mistaken for a confident claim.
      const exhaustiveCheck: never = status;
      return { variant: "default", label: `Basis: ${exhaustiveCheck as string}` };
    }
  }
}
