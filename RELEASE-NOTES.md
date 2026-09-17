# dashboard-maker 1.1.0

## Added

- **Edit a service.** Services could be added and deleted but never changed. Cards now carry an edit button in edit mode that opens the panel prefilled; saving updates in place via `PUT /api/services/<id>`.
- **Service icons.** Upload an icon from the service panel (`POST /api/images`) and it renders on the card. Filenames are sanitised, extensions allowlisted, and repeat names are suffixed rather than overwriting an icon another service uses.
- **Rename categories**, with every service in them following the rename (`PUT /api/categories/<name>`).
- **Safer category deletion.** Deleting a category that still holds services now asks where they should go instead of silently orphaning them (`DELETE /api/categories/<name>?reassign=<target>`).
- **Drag to reorder** service cards within a category (`POST /api/services/reorder`).
- **Reachability indicator** per service, from a new `GET /api/status`. Checks run server-side, in parallel, cached for 30 seconds. Any response counts as up; self-signed certificates are accepted.
- **Search box** filtering on name, description, URL and category.

## Fixed

- **Path traversal in `/images/<path>`.** `GET /images/../etc/passwd` returned the file. Now served through `send_from_directory`, which refuses paths outside the images directory.
- **Unescaped values in rendered markup.** A service name containing `<` or a category containing `"` broke the surrounding markup — a quoted category silently lost its Remove button. All values are escaped now.
- **Non-atomic JSON writes.** `services.json` was written in place, so an interrupted write could truncate it. Writes now go to a temp file and are renamed into place.

## Changed

- Service and category actions re-render in place instead of reloading the whole page. Theme switching still reloads, since the theme is the document.
- Clicking a card while in edit mode no longer navigates away, so dragging can't trigger a stray navigation. Normal mode is unchanged.
- Dragging is disabled while a search filter is active, because a filtered grid is only part of the list.

## Notes for theme authors

No theme HTML changed. The new controls, dialogs and their CSS are injected at runtime by `dashboard.js` and styled with each theme's existing variables, so custom themes already saved in `/data/themes` pick everything up without being edited.

## Upgrading

Drop-in, and nothing in `/data` or `/images` is rewritten on startup. Pull the new image and recreate the container against the same volumes.

- `services.json`, `categories.json` and `config.json` keep their formats. `icon` is a new optional field on a service; entries without one render exactly as before.
- Custom themes in `/data/themes` are untouched, and keep working unmodified — the new controls are injected at runtime, so a theme cloned under 1.0.0 gains them without being edited.
- Existing files in `/images` are left alone. Uploading an icon whose name already exists adds a suffix rather than overwriting.
- File permissions and ownership in `/data` are preserved when a file is rewritten, so backup scripts and bind mounts read by another user keep working.
- If you bind-mount an individual JSON file rather than the directory, saving still works.
- Tailwind and the Inter font are now served from the image instead of a CDN. Themes already saved in `/data/themes` are rewritten as they are served, so they get this too and their files are left unmodified.

Roll back at any time with `randomsi/dashboard-maker:1.0.0` — 1.1.0 writes nothing that 1.0.0 cannot read.

## License

MIT. See `LICENSE`, which ships inside the image at `/app/LICENSE`.
