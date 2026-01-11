
# App Integration Notes (Free v1)

Free v1 is designed so that **fp-lite** can run offline or inside a mobile app.

## Minimal flow
1. CPE exports `evidence_bundle_*.json` after OBH is pressed.
2. App downloads the bundle via an existing secure channel (vendor-defined).
3. App runs fp-lite locally and displays:
   - before/during/after summary
   - delta vector
   - pattern label + confidence
4. App never changes CPE settings in Free v1.

## Security & privacy
- Bundle is metadata-only.
- No payload inspection.
- Bundle is scoped to last 60 minutes.
