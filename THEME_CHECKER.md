# Theme Toggle - Diagnostic Checklist

## ✅ Quick Verification Steps

### 1. **Check Theme Toggle Button Exists**
- [ ] Open any page (Dashboard, Patients, Integrations)
- [ ] Look at **top-right header** (next to user avatar)
- [ ] Should see a **sun/moon icon button**

### 2. **Test Theme Toggle**
- [ ] Click the sun/moon button
- [ ] Dropdown should appear with 3 options:
  - ☀️ Light
  - 🌙 Dark
  - 🖥️ System
- [ ] Click each option and verify UI changes

### 3. **Visual Check - Light Mode**
When "Light" is selected:
- [ ] Background: **White/Gray-50** (not dark)
- [ ] Sidebar: **White** background
- [ ] Header: **White** background
- [ ] Cards: **White** backgrounds
- [ ] Text: **Dark gray/black** (readable)
- [ ] Borders: **Light gray** (subtle)

### 4. **Visual Check - Dark Mode**
When "Dark" is selected:
- [ ] Background: **Dark slate-900**
- [ ] Sidebar: **Dark gradient** (slate-900/800)
- [ ] Header: **Dark slate-800**
- [ ] Cards: **Semi-transparent slate-800**
- [ ] Text: **White/light gray** (readable)
- [ ] Borders: **Dark slate-700** (visible)

### 5. **Visual Check - System Mode**
When "System" is selected:
- [ ] Matches your **OS theme**
- [ ] Changes automatically when **OS theme changes**

---

## 🔍 Common Issues & Fixes

### Issue 1: Toggle Button Not Visible
**Symptom:** Can't find sun/moon icon in header

**Check:**
```bash
# Verify ThemeToggle is imported in Header
grep -n "ThemeToggle" frontend/src/components/layout/Header.tsx
```

**Fix:** Already implemented in `Header.tsx` line 18

---

### Issue 2: Theme Not Switching
**Symptom:** Click toggle but UI doesn't change

**Diagnosis:**
1. Open browser DevTools (F12)
2. Check Console for errors
3. Check `<html>` tag has class:
   ```html
   <html class="dark"> or <html class="light">
   ```

**Common Causes:**
- [ ] localStorage blocked (private browsing)
- [ ] JavaScript error preventing state update
- [ ] CSS not loaded

**Fix:**
```bash
# Clear browser cache and localStorage
# Then reload page (Cmd+Shift+R / Ctrl+Shift+F5)
```

---

### Issue 3: Some Elements Not Changing
**Symptom:** Some parts stay dark/light when toggling

**Cause:** Component using hardcoded classes instead of `dark:` variants

**How to Check:**
1. Inspect element in DevTools
2. Look for classes like:
   - ❌ `bg-slate-800` (always dark)
   - ✅ `bg-white dark:bg-slate-800` (theme-aware)

**Pages Already Fixed:**
- ✅ Dashboard layout
- ✅ Patients page
- ✅ Integrations page
- ⚠️ Medicine Library (partially)
- ⚠️ Payments (partially)

---

### Issue 4: Flash of Wrong Theme
**Symptom:** Page loads in wrong theme briefly, then switches

**Cause:** Theme applied after page render

**Check:**
```tsx
// In src/app/layout.tsx, verify:
<html suppressHydrationWarning>
```

**Fix:** Already implemented ✅

---

### Issue 5: Theme Not Persisting
**Symptom:** Theme resets on page reload

**Diagnosis:**
1. Open DevTools → Application → Local Storage
2. Check for key: `theme-storage`
3. Should contain: `{"state":{"theme":"dark",...}}`

**Causes:**
- [ ] Private browsing mode
- [ ] Browser blocking localStorage
- [ ] Different origin/port

**Fix:** Use normal browser window (not incognito)

---

## 🧪 Browser DevTools Testing

### Check HTML Class
```javascript
// Open DevTools Console (F12)
// Check current theme class
document.documentElement.className
// Should show: "... dark ..." or "... light ..."
```

### Check Theme Store
```javascript
// Check Zustand store state
localStorage.getItem('theme-storage')
// Should show JSON with theme: "light" | "dark" | "system"
```

### Check CSS Variables
```javascript
// Check if CSS variables are defined
getComputedStyle(document.documentElement).getPropertyValue('--background')
// Should show RGB values
```

### Manually Toggle Theme
```javascript
// Force dark mode
document.documentElement.classList.remove('light')
document.documentElement.classList.add('dark')

// Force light mode
document.documentElement.classList.remove('dark')
document.documentElement.classList.add('light')
```

---

## 🎨 Visual Indicators by Page

### Dashboard Page
**Light Mode:**
- Background: Light gray (bg-gray-50)
- Cards: White
- Quick Actions: Light with dashed border

**Dark Mode:**
- Background: Dark slate gradient
- Cards: Semi-transparent slate
- Quick Actions: Dark with subtle glow

### Patients Page
**Light Mode:**
- Search bar: White background
- Stats cards: White
- Patient cards: White with gray borders

**Dark Mode:**
- Search bar: Dark slate-900
- Stats cards: Semi-transparent slate
- Patient cards: Glass effect

### Integrations Page
**Light Mode:**
- Provider cards: White
- Badges: Pastel colors (blue-100, green-100)
- Buttons: White outlines

**Dark Mode:**
- Provider cards: Semi-transparent slate
- Badges: Transparent with borders
- Buttons: Slate with light text

---

## 🔧 Manual Testing Script

Run this in your browser console to test theme functionality:

```javascript
// 1. Check if theme store exists
const hasThemeStore = Boolean(localStorage.getItem('theme-storage'))
console.log('Theme Store Exists:', hasThemeStore)

// 2. Check current theme
const currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light'
console.log('Current Theme:', currentTheme)

// 3. Test toggle
const originalTheme = currentTheme
document.documentElement.classList.toggle('dark')
document.documentElement.classList.toggle('light')
console.log('Theme Toggled:', document.documentElement.className)

// 4. Restore original
document.documentElement.classList.remove('dark', 'light')
document.documentElement.classList.add(originalTheme)
console.log('Theme Restored:', originalTheme)

// 5. Check if transitions are working
console.log('CSS Transitions:', getComputedStyle(document.body).transitionDuration)
```

---

## 📱 Mobile Testing

### iOS Safari
- [ ] Theme toggle button visible
- [ ] Dropdown works
- [ ] Meta theme-color changes (status bar)
- [ ] Smooth transitions

### Android Chrome
- [ ] Theme toggle button visible
- [ ] Dropdown works
- [ ] Meta theme-color changes (address bar)
- [ ] Smooth transitions

---

## 🚨 Known Limitations

1. **First Load Flash**
   - Very brief flash may occur on first visit
   - Normal behavior due to SSR/hydration
   - Minimized with `suppressHydrationWarning`

2. **System Theme Detection**
   - Requires modern browser
   - May not work in older browsers
   - Falls back to dark mode

3. **Third-Party Components**
   - Some UI libraries may not support dark mode
   - Currently using shadcn/ui (supports dark mode ✅)

---

## ✅ Expected Behavior

### Correct Functionality:
1. **Toggle Opens:** Click button → dropdown appears
2. **Theme Changes:** Select option → UI updates immediately
3. **Smooth Transition:** 200ms animated color change
4. **Persistence:** Reload page → theme stays same
5. **System Sync:** Change OS theme → app follows (if System mode)

### Incorrect (Needs Fix):
1. **No Visual Change:** Selected theme but UI didn't update
2. **Partial Update:** Some elements changed, others didn't
3. **Flash on Load:** Page shows wrong theme briefly
4. **No Persistence:** Theme resets on reload

---

## 🎯 Quick Fix Commands

### If Theme Stuck:
```javascript
// Clear theme storage
localStorage.removeItem('theme-storage')
// Reload page
location.reload()
```

### Force Rebuild:
```bash
# Stop dev server
# Clear Next.js cache
rm -rf frontend/.next

# Restart
cd frontend && npm run dev
```

### Reset Everything:
```bash
# Clear all browser data for localhost:3000
# Or use incognito mode for fresh start
```

---

## 📊 Success Criteria

Your theme system is working correctly if:

- ✅ Toggle button visible in header
- ✅ All 3 modes selectable
- ✅ UI changes immediately on selection
- ✅ Changes are smooth (no jarring flash)
- ✅ Theme persists after reload
- ✅ System mode follows OS preference
- ✅ All text is readable in both modes
- ✅ All interactive elements visible

---

## 🔮 Advanced Debugging

### React DevTools
1. Install React DevTools extension
2. Check component tree
3. Look for `ThemeProvider` component
4. Verify `useThemeStore` hook values

### Performance Check
```javascript
// Measure theme switch time
console.time('themeSwitch')
document.documentElement.classList.toggle('dark')
document.documentElement.classList.toggle('light')
console.timeEnd('themeSwitch')
// Should be < 100ms
```

### Accessibility Check
```javascript
// Check contrast ratios (should be > 4.5:1)
// Use browser DevTools → Lighthouse → Accessibility
```

---

**Need Help?**
If theme toggle still not working after these checks, share:
1. Browser console errors
2. Screenshot of the issue
3. Which page you're testing
4. Current theme mode selected
