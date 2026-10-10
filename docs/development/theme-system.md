# Theme System — Light / Dark

AltCare has **two themes: light and dark**, switched with a single button in the header. There is
deliberately **no "System" mode**: the app never follows the operating system's preference. New
visitors start in **light**.

## Where things live

| File | Role |
|---|---|
| `frontend/src/store/themeStore.ts` | Zustand store, persisted to `localStorage` key `theme-storage`. `theme: 'light' \| 'dark'`, `setTheme`, `toggleTheme`. `applyTheme()` sets the `light`/`dark` class on `<html>` and the mobile `theme-color` meta tag. |
| `frontend/src/components/theme/ThemeToggle.tsx` | The header button (shows the mode you would switch *to*; `aria-label` says so). |
| `frontend/src/components/theme/ThemeProvider.tsx` | Keeps `<html>` in step with the stored theme. |
| `frontend/src/app/layout.tsx` | Inline script that applies the stored theme **before first paint** (no flash). |
| `frontend/src/app/globals.css` | Color tokens: `:root` (light) and `.dark`. Tailwind's `dark:` variant keys off the `.dark` class. |

## Behavior

- **Default:** light. The OS color scheme is ignored.
- **Persistence:** the choice is remembered per browser.
- **Migration:** earlier versions stored `'system'`. Such a value is resolved **once** against the OS
  at load (so nobody's look changes suddenly) and from then on is a plain light or dark choice
  (store `version: 1`, `migrate`). The inline script in `layout.tsx` applies the same rule.
- **No flash:** the class is set by the inline script in `<head>` before React hydrates.

## Dark-mode color notes

The dark `--primary` is emerald-700 (`#047857`) rather than the light theme's navy, which would be
identical to the dark page background (1:1 contrast). Measured: button vs page 3.26:1, label text
5.48:1. Primary buttons with a hard-coded `hover:bg-slate-950` also set `dark:hover:bg-emerald-800`.

## Testing checklist

1. Fresh profile (clear `theme-storage`) → light, even if the OS is in dark mode.
2. Click the toggle → dark; reload → still dark, no flash.
3. Click again → light; reload → still light.
4. Set `theme-storage` to `{"state":{"theme":"system"},"version":0}` with an OS in dark mode →
   loads dark once, then behaves as a normal stored choice.
