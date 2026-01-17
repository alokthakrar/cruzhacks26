# Frontend Testing Guide

Manual verification guide for the OCR-first canvas interface.

## Prerequisites

1. **Backend server running:**
   ```bash
   cd ../backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend dev server running:**
   ```bash
   npm run dev
   ```

3. **Backend dependencies installed and Gemini API configured** (see backend/TESTING.md)

## Manual Testing Checklist

### 1. Canvas Rendering ✓

**Navigate to:** http://localhost:3000/canvas

**Verify:**
- [ ] Canvas loads without errors
- [ ] No hydration warnings in console
- [ ] Canvas is interactive (can draw)
- [ ] Controls are visible and responsive

### 2. Drawing Controls ✓

**Test:**
- [ ] Draw on canvas with mouse/touch
- [ ] Change stroke color - verify color changes
- [ ] Adjust stroke width slider - verify width changes
- [ ] Click "Undo" - last stroke removed
- [ ] Click "Redo" - stroke restored
- [ ] Click "Clear" - entire canvas cleared

### 3. OCR Analysis Flow ✓

**Test Case 1: Simple Expression**

1. Draw a simple expression: `x^2 + 5`
2. Click "✓ Check My Work"
3. **Verify loading states:**
   - [ ] Button shows "📖 Reading handwriting..."
   - [ ] Then shows "🤔 Analyzing logic..."
   - [ ] Controls disabled during loading
4. **Verify results appear:**
   - [ ] "👁️ What AI Saw" section displays
   - [ ] LaTeX string shown in code box
   - [ ] LaTeX rendered mathematically (not plain text)
   - [ ] OCR confidence percentage displayed
   - [ ] AI feedback section appears
   - [ ] Feedback text is relevant

**Test Case 2: Math Problem**

1. Clear canvas
2. Draw: `∫ x^2 dx`
3. Click "✓ Check My Work"
4. **Verify:**
   - [ ] LaTeX detection works for integral symbol
   - [ ] AI suggests adding "+ C"
   - [ ] Hints section appears with suggestions
   - [ ] Error type tags shown (if applicable)

**Test Case 3: Correct Answer**

1. Clear canvas
2. Draw: `2 + 2 = 4`
3. Click "✓ Check My Work"
4. **Verify:**
   - [ ] "✅ Looking Good!" or positive feedback
   - [ ] Green-tinted feedback box
   - [ ] No hints (or minimal hints)

**Test Case 4: Blank Canvas**

1. Clear canvas (leave empty)
2. Click "✓ Check My Work"
3. **Verify:**
   - [ ] Error message or "No text detected" feedback
   - [ ] Hints suggest writing more clearly
   - [ ] No crash or 500 error

### 4. Error Handling ✓

**Test Case 1: Backend Down**

1. Stop backend server
2. Draw something and click "✓ Check My Work"
3. **Verify:**
   - [ ] Red error box appears
   - [ ] Error message describes connection issue
   - [ ] UI doesn't crash

**Test Case 2: Bad Handwriting**

1. Draw messy, illegible marks
2. Click "✓ Check My Work"
3. **Verify:**
   - [ ] OCR error message shows
   - [ ] Feedback suggests clearer writing
   - [ ] No crash

### 5. UI/UX Verification ✓

**Responsive Design:**
- [ ] Page looks good on desktop (1920x1080)
- [ ] Controls wrap properly on smaller screens
- [ ] Canvas remains usable on tablet size (768px)

**Accessibility:**
- [ ] Button states are clear (enabled/disabled)
- [ ] Color contrast is readable
- [ ] Loading states are obvious

**Performance:**
- [ ] Drawing is smooth (no lag)
- [ ] Analysis completes in < 10 seconds
- [ ] No memory leaks (check DevTools Performance)

### 6. LaTeX Rendering ✓

**Test various LaTeX expressions:**

1. **Fractions:** Draw `x/2` or `1/2`
   - [ ] Renders as stacked fraction

2. **Exponents:** Draw `x^2`
   - [ ] Renders with superscript

3. **Integrals:** Draw `∫ x dx`
   - [ ] Integral symbol renders correctly

4. **Complex:** Draw `∫ x^2 dx = x^3/3 + C`
   - [ ] Entire expression renders properly

## Browser Testing

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Safari (WebKit)
- [ ] Firefox

## Console Checks

Open browser DevTools Console and verify:
- [ ] No red errors
- [ ] No hydration warnings
- [ ] No 404s or failed network requests
- [ ] API requests show correct payload

**Expected console output after analysis:**
```javascript
// No errors
// Successful POST to http://localhost:8000/api/analyze/ocr_first
```

## Network Tab Verification

1. Open DevTools → Network tab
2. Draw and click "Check My Work"
3. **Verify request:**
   - [ ] Method: POST
   - [ ] URL: http://localhost:8000/api/analyze/ocr_first
   - [ ] Content-Type: multipart/form-data
   - [ ] Request includes image file
   - [ ] Response status: 200
   - [ ] Response contains: latex_string, feedback, hints

## Screenshot Verification

Take screenshots of:
1. ✅ Initial canvas state
2. ✅ Canvas with drawing
3. ✅ Loading state ("Reading handwriting...")
4. ✅ "What AI Saw" section with LaTeX
5. ✅ AI feedback with hints
6. ✅ Error state (backend down)

## Automated Testing (Optional)

For automated testing, consider adding:

```bash
# Install Playwright
npm install -D @playwright/test

# Run E2E tests
npx playwright test
```

See Playwright documentation for setup: https://playwright.dev/

## Known Issues / Expected Behavior

1. **First OCR call slow:** Pix2Text model loads on first use (1-3 seconds)
2. **Gemini not configured:** AI feedback shows "unavailable" message (graceful degradation)
3. **Messy handwriting:** OCR may misread - this is expected, verify "What AI Saw" catches it
4. **Complex math:** Very complex LaTeX may not render perfectly - this is a known limitation

## Success Criteria

All tests pass when:
- ✅ Canvas is interactive and responsive
- ✅ OCR detects handwritten math
- ✅ "What AI Saw" accurately shows OCR output
- ✅ LaTeX renders correctly
- ✅ AI provides relevant feedback
- ✅ Errors are handled gracefully
- ✅ Loading states are clear
- ✅ No console errors or warnings
