# Modal Architecture Documentation

**Version:** 1.0
**Last Updated:** 2025-11-14
**Component:** GlassModal System

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Structure](#component-structure)
4. [Modal Types](#modal-types)
5. [State Management](#state-management)
6. [Event Lifecycle](#event-lifecycle)
7. [Accessibility Features](#accessibility-features)
8. [Responsive Behavior](#responsive-behavior)
9. [API Reference](#api-reference)
10. [Known Edge Cases](#known-edge-cases)

---

## Overview

The **GlassModal** system is an enterprise-grade modal management library built with **vanilla JavaScript** and styled with **glassmorphic design principles**. It provides a consistent, accessible, and performant modal experience across the application.

### Design Philosophy

1. **Accessibility First:** WCAG AA compliant with full keyboard navigation
2. **Progressive Enhancement:** Works without JavaScript (graceful degradation)
3. **Performance Optimized:** Hardware-accelerated animations, minimal DOM manipulation
4. **Mobile-First:** Touch-optimized with virtual keyboard detection
5. **Framework Agnostic:** Pure JavaScript, no dependencies

### Key Features

✅ **Keyboard Navigation** — Tab, Shift+Tab, Esc with focus trapping
✅ **ARIA Compliance** — role="dialog", aria-modal, aria-labelledby
✅ **Stack Management** — Support for multiple modals
✅ **Event Hooks** — onShow, onShown, onHide, onHidden callbacks
✅ **Responsive** — Mobile slides from bottom, desktop centered
✅ **Virtual Keyboard Detection** — Auto-resize on mobile
✅ **Glassmorphic Design** — Backdrop blur, transparency, depth

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GlassModal System                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │            GlassModal Class                     │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │ Static Properties                        │  │    │
│  │  │ - instances[]  (all modal instances)     │  │    │
│  │  │ - stack[]      (open modals)             │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  │                                                 │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │ Instance Properties                      │  │    │
│  │  │ - modal        (DOM element)             │  │    │
│  │  │ - dialog       (.modal-dialog)           │  │    │
│  │  │ - content      (.modal-content)          │  │    │
│  │  │ - backdrop     (overlay element)         │  │    │
│  │  │ - isOpen       (boolean state)           │  │    │
│  │  │ - focusableElements  (array)             │  │    │
│  │  │ - previouslyFocusedElement               │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  │                                                 │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │ Public Methods                           │  │    │
│  │  │ - show()       - Open modal              │  │    │
│  │  │ - hide()       - Close modal             │  │    │
│  │  │ - toggle()     - Toggle state            │  │    │
│  │  │ - setContent() - Update body             │  │    │
│  │  │ - setTitle()   - Update title            │  │    │
│  │  │ - destroy()    - Remove instance          │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  │                                                 │    │
│  │  ┌──────────────────────────────────────────┐  │    │
│  │  │ Private Methods                          │  │    │
│  │  │ - init()                                 │  │    │
│  │  │ - createBackdrop()                       │  │    │
│  │  │ - bindEvents()                           │  │    │
│  │  │ - handleKeyDown()                        │  │    │
│  │  │ - handleTabKey()                         │  │    │
│  │  │ - updateFocusableElements()              │  │    │
│  │  │ - detectVirtualKeyboard()                │  │    │
│  │  └──────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │            Static Methods                       │    │
│  │ - getInstance()  - Get or create instance      │    │
│  │ - create()       - Create modal from config    │    │
│  │ - confirm()      - Show confirm dialog         │    │
│  │ - alert()        - Show alert dialog           │    │
│  │ - hideAll()      - Close all open modals       │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

#### Opening a Modal

```
User Action (button click, programmatic call)
    ↓
modal.show() called
    ↓
onShow callback executed
    ↓
Store currently focused element
    ↓
Prevent body scroll (add .modal-open class)
    ↓
Show backdrop (add .show class)
    ↓
Show modal (add .show class)
    ↓
Update ARIA attributes (aria-hidden="false")
    ↓
Update focusable elements list
    ↓
Set focus to first focusable element
    ↓
Bind keyboard event listeners
    ↓
Add to modal stack
    ↓
onShown callback executed (after 200ms transition)
```

#### Closing a Modal

```
User Action (Esc key, close button, backdrop click)
    ↓
modal.hide() called
    ↓
onHide callback executed
    ↓
Remove .show class from modal
    ↓
Update ARIA attributes (aria-hidden="true")
    ↓
Hide backdrop (remove .show class)
    ↓
Remove from modal stack
    ↓
Allow body scroll if no other modals open
    ↓
Unbind keyboard event listeners
    ↓
Restore focus to previously focused element
    ↓
onHidden callback executed (after 200ms transition)
```

---

## Component Structure

### HTML Structure

```html
<!-- Modal Container -->
<div class="modal" id="exampleModal" tabindex="-1" role="dialog" aria-modal="true" aria-hidden="true">

  <!-- Modal Dialog Wrapper -->
  <div class="modal-dialog modal-lg">

    <!-- Glassmorphic Content Card -->
    <div class="modal-content">

      <!-- Header -->
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">
          <i class="bi bi-icon"></i> Modal Title
        </h5>
        <button type="button" class="btn-close" data-dismiss="modal" aria-label="Close">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- Body -->
      <div class="modal-body">
        <!-- Content goes here -->
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">
          Cancel
        </button>
        <button type="button" class="btn btn-primary">
          Save
        </button>
      </div>

    </div>
  </div>
</div>

<!-- Backdrop (created programmatically) -->
<div class="modal-backdrop"></div>
```

### CSS Class Hierarchy

```
.modal                        // Container (fixed, full-screen)
├── .modal-dialog            // Centering wrapper
│   ├── .modal-dialog-sm     // Small size (480px)
│   ├── .modal-dialog-lg     // Large size (960px)
│   ├── .modal-dialog-xl     // Extra large (1200px)
│   └── .modal-dialog-fullscreen  // Full screen
│
└── .modal-content           // Glassmorphic card
    ├── .glass-dark          // Dark variant
    ├── .modal-header
    │   ├── .modal-title
    │   └── .btn-close
    ├── .modal-body
    └── .modal-footer
        ├── .modal-footer-start
        └── [buttons]

.modal-backdrop              // Overlay (separate element)
```

### State Classes

| Class | Applied To | Purpose |
|-------|-----------|---------|
| `.show` | `.modal`, `.modal-backdrop` | Visible state |
| `.modal-open` | `<body>` | Prevent scroll when modal open |
| `.keyboard-visible` | `.modal` | Virtual keyboard detected (mobile) |
| `.active` | (varies) | Interactive state |

---

## Modal Types

### 1. Template Modal (Create/Edit)

**Purpose:** Form for creating or editing templates

**Configuration:**

```javascript
GlassModal.create({
  type: 'template',
  size: 'lg',
  title: '<i class="bi bi-file-earmark-plus"></i> Create Template',
  body: `<form>...</form>`,
  footer: `
    <div class="modal-footer-start">
      <div class="saving-indicator">Saving...</div>
    </div>
    <button class="btn btn-secondary" data-dismiss="modal">Cancel</button>
    <button class="btn btn-primary">Save</button>
  `
});
```

**Features:**

- Large size (720px)
- Autosave indicator in footer
- AI validation button
- Character counters
- Tag input
- Form validation

**Visual:**

```
┌──────────────────────────────────────────────────────┐
│ 📄 Create Template                               ✕   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Title: [_________________________________]  200/200  │
│                                                       │
│  Description:                                         │
│  [__________________________________________]         │
│  [__________________________________________]         │
│                                                       │
│  Domain: [Marketing ▼]   Visibility: [Private ▼]     │
│                                                       │
│  Prompt Body:                                         │
│  [__________________________________________]         │
│  [__________________________________________]         │
│  [__________________________________________]         │
│  [__________________________________________]         │
│                                                       │
│  Tags: [marketing] [email] [+]                        │
│                                                       │
├──────────────────────────────────────────────────────┤
│  💾 Saving...              [Cancel] [💾 Save]         │
└──────────────────────────────────────────────────────┘
```

### 2. Delete Confirmation Modal

**Purpose:** Confirm destructive actions

**Configuration:**

```javascript
const confirmed = await GlassModal.confirm({
  title: 'Delete Template',
  message: 'Are you sure you want to delete this template?',
  confirmText: 'Delete',
  cancelText: 'Cancel',
  confirmClass: 'btn-danger',
  icon: 'bi-trash'
});
```

**Features:**

- Small size (480px)
- Red accent border
- Large icon
- Promise-based API
- Auto-cleanup on close

**Visual:**

```
┌──────────────────────────────┐
│ 🗑️ Delete Template        ✕  │
├──────────────────────────────┤
│                               │
│         ⚠️                    │
│                               │
│  Are you sure you want to    │
│  delete this template?       │
│  This action cannot be       │
│  undone.                     │
│                               │
├──────────────────────────────┤
│    [Cancel] [🗑️ Delete]      │
└──────────────────────────────┘
```

### 3. Preview Modal

**Purpose:** Read-only template view with copy functionality

**Configuration:**

```javascript
GlassModal.create({
  type: 'preview',
  size: 'lg',
  title: '<i class="bi bi-eye"></i> Template Preview',
  body: `
    <div class="preview-content">
      <button class="copy-button">📋 Copy</button>
      <pre><code>${promptBody}</code></pre>
    </div>
  `
});
```

**Features:**

- Large size (960px)
- Syntax highlighting
- Copy-to-clipboard button
- Metadata display (tags, domain)
- Scrollable content area

**Visual:**

```
┌────────────────────────────────────────────────┐
│ 👁️ Marketing Email Generator              ✕   │
├────────────────────────────────────────────────┤
│                              [📋 Copy]         │
│  ┌──────────────────────────────────────────┐ │
│  │ You are a professional email copywriter  │ │
│  │ specializing in marketing campaigns...   │ │
│  │                                           │ │
│  │ Generate a compelling email that:        │ │
│  │ 1. Grabs attention with subject line     │ │
│  │ 2. Provides clear value proposition      │ │
│  │ 3. Includes strong call-to-action        │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Tags: [marketing] [email] [copywriting]       │
│  Domain: Marketing                             │
│                                                │
├────────────────────────────────────────────────┤
│                [Close] [▶️ Use Template]        │
└────────────────────────────────────────────────┘
```

### 4. Feedback Modal (AI Validation)

**Purpose:** Display AI validation results and quality metrics

**Configuration:**

```javascript
GlassModal.create({
  type: 'feedback',
  size: 'md',
  title: '<i class="bi bi-cpu"></i> AI Validation',
  body: `
    <div class="quality-score">
      <div class="score-circle" style="--score: 85">85</div>
    </div>
    <ul class="feedback-list">
      <li class="feedback-item success">✅ Clear objective</li>
      <li class="feedback-item warning">⚠️ Add more context</li>
    </ul>
  `
});
```

**Features:**

- Medium size (600px)
- Circular progress indicator
- Color-coded feedback items
- Suggestions section
- Auto-update via SSE

**Visual:**

```
┌──────────────────────────────────────┐
│ 🖥️ AI Validation                  ✕ │
├──────────────────────────────────────┤
│                                      │
│             ╱───────╲                │
│           ╱           ╲              │
│          │     85      │             │
│           ╲           ╱              │
│             ╲───────╱                │
│                                      │
│  Quality Analysis:                   │
│                                      │
│  ✅ Clear objective stated           │
│  ✅ Good use of examples             │
│  ⚠️ Could add more context           │
│  ℹ️ Consider role specification      │
│                                      │
│  Suggestions:                        │
│  💡 Add output format constraints    │
│                                      │
├──────────────────────────────────────┤
│                       [Close]         │
└──────────────────────────────────────┘
```

---

## State Management

### Modal State

Each modal instance maintains internal state:

```javascript
{
  modal: HTMLElement,                // Modal DOM element
  dialog: HTMLElement,               // .modal-dialog
  content: HTMLElement,              // .modal-content
  backdrop: HTMLElement,             // Backdrop element
  isOpen: boolean,                   // Current state
  previouslyFocusedElement: Element, // For focus restoration
  focusableElements: Array,          // Tab-able elements
  firstFocusableElement: Element,    // First in tab order
  lastFocusableElement: Element,     // Last in tab order
  options: {
    keyboard: true,
    backdrop: true,
    focus: true,
    closeOnBackdrop: true,
    scrollable: false,
    onShow: Function,
    onShown: Function,
    onHide: Function,
    onHidden: Function
  }
}
```

### Global State

```javascript
GlassModal.instances = [
  // All modal instances
];

GlassModal.stack = [
  // Currently open modals (LIFO order)
];
```

### State Transitions

```
┌─────────────┐
│  Closed     │
│  (initial)  │
└──────┬──────┘
       │ show()
       ▼
┌─────────────┐
│  Opening    │
│  (200ms)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Open       │
│  (stable)   │
└──────┬──────┘
       │ hide()
       ▼
┌─────────────┐
│  Closing    │
│  (200ms)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Closed     │
└─────────────┘
```

---

## Event Lifecycle

### Event Flow

```
┌─────────────────────────────────────────────────────────┐
│                    MODAL SHOW                            │
├─────────────────────────────────────────────────────────┤
│  1. show() method called                                 │
│     ↓                                                    │
│  2. onShow callback (immediate)                          │
│     ↓                                                    │
│  3. Store previous focus                                 │
│     ↓                                                    │
│  4. Prevent body scroll                                  │
│     ↓                                                    │
│  5. Show backdrop (add .show class)                      │
│     ↓                                                    │
│  6. Show modal (add .show class)                         │
│     ↓                                                    │
│  7. Update ARIA (aria-hidden="false")                    │
│     ↓                                                    │
│  8. Update focusable elements                            │
│     ↓                                                    │
│  9. Set focus (100ms delay)                              │
│     ↓                                                    │
│  10. Bind keyboard listeners                             │
│     ↓                                                    │
│  11. Add to modal stack                                  │
│     ↓                                                    │
│  12. onShown callback (after 200ms transition)           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    MODAL HIDE                            │
├─────────────────────────────────────────────────────────┤
│  1. hide() method called                                 │
│     ↓                                                    │
│  2. onHide callback (immediate)                          │
│     ↓                                                    │
│  3. Remove .show class from modal                        │
│     ↓                                                    │
│  4. Update ARIA (aria-hidden="true")                     │
│     ↓                                                    │
│  5. Hide backdrop (remove .show class)                   │
│     ↓                                                    │
│  6. Remove from modal stack                              │
│     ↓                                                    │
│  7. Allow body scroll (if stack empty)                   │
│     ↓                                                    │
│  8. Unbind keyboard listeners                            │
│     ↓                                                    │
│  9. Restore focus to previous element                    │
│     ↓                                                    │
│  10. onHidden callback (after 200ms transition)          │
└─────────────────────────────────────────────────────────┘
```

### Custom Event Hooks

```javascript
const modal = GlassModal.create({
  title: 'My Modal',

  // Called immediately when show() is invoked
  onShow: (modalInstance) => {
    console.log('Modal is about to show');
    // Use case: Fetch data, initialize components
  },

  // Called after modal is fully visible (200ms after show)
  onShown: (modalInstance) => {
    console.log('Modal is fully visible');
    // Use case: Set focus to specific element, start animation
  },

  // Called immediately when hide() is invoked
  onHide: (modalInstance) => {
    console.log('Modal is about to hide');
    // Use case: Cleanup, save state
  },

  // Called after modal is fully hidden (200ms after hide)
  onHidden: (modalInstance) => {
    console.log('Modal is fully hidden');
    // Use case: Destroy modal, free resources
  }
});
```

---

## Accessibility Features

### ARIA Attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `role` | `dialog` | Identifies as dialog |
| `aria-modal` | `true` | Indicates modal behavior |
| `aria-labelledby` | `{modalTitleId}` | Associates with title |
| `aria-describedby` | `{modalBodyId}` | Associates with description |
| `aria-hidden` | `true/false` | Visibility for screen readers |
| `tabindex` | `-1` | Allows programmatic focus |

### Focus Management

**Focus Trap Implementation:**

```javascript
handleTabKey(e) {
  const isTabForward = !e.shiftKey;
  const activeElement = document.activeElement;

  // Forward tab on last element → go to first
  if (isTabForward && activeElement === this.lastFocusableElement) {
    e.preventDefault();
    this.firstFocusableElement.focus();
  }

  // Backward tab on first element → go to last
  if (!isTabForward && activeElement === this.firstFocusableElement) {
    e.preventDefault();
    this.lastFocusableElement.focus();
  }
}
```

**Focusable Elements:**

```javascript
const focusableSelectors = [
  'a[href]',
  'button:not([disabled])',
  'textarea:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]'
];
```

### Keyboard Shortcuts

| Key Combination | Action |
|-----------------|--------|
| `Esc` | Close modal |
| `Tab` | Move focus forward (with trap) |
| `Shift + Tab` | Move focus backward (with trap) |
| `Enter` | Activate focused button/link |
| `Space` | Activate focused button |

### Screen Reader Announcements

**Modal Open:**

```
"Dialog opened: Create Template. Use Escape to close."
```

**Modal Close:**

```
"Dialog closed. Focus restored to [previous element]."
```

**Form Validation:**

```
"Error: This field is required."
"Warning: Title is too long. 250 of 200 characters."
```

---

## Responsive Behavior

### Desktop (≥ 769px)

- **Position:** Centered vertically and horizontally
- **Animation:** Fade in + scale (0.95 → 1.0)
- **Size:** Fixed width (480px, 720px, 960px, 1200px)
- **Backdrop:** Blurred overlay, click to close
- **Scroll:** Modal body scrolls, page locked

**CSS:**

```css
@media (min-width: 769px) {
  .modal {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-dialog {
    max-width: 720px;
    transform: scale(0.95) translateY(20px);
  }

  .modal.show .modal-dialog {
    transform: scale(1) translateY(0);
  }
}
```

### Tablet (481px - 768px)

- **Position:** Centered with margins
- **Size:** 90% of viewport width
- **Animation:** Fade in + subtle scale
- **Behavior:** Same as desktop

### Mobile (≤ 480px)

- **Position:** Slides from bottom
- **Animation:** Translate Y (100% → 0)
- **Size:** Full width, max-height 90vh
- **Border Radius:** Top corners only (2rem)
- **Virtual Keyboard:** Auto-resize on detection

**CSS:**

```css
@media (max-width: 768px) {
  .modal {
    align-items: flex-end;
    padding: 0;
  }

  .modal-dialog {
    max-width: 100%;
    margin: 0;
    transform: translateY(100%);
  }

  .modal.show .modal-dialog {
    transform: translateY(0);
  }

  .modal-content {
    border-radius: var(--radius-xl) var(--radius-xl) 0 0;
    max-height: 90vh;
  }
}
```

### Virtual Keyboard Detection

**Problem:** Virtual keyboard on mobile reduces available viewport height, potentially cutting off modal content.

**Solution:** Detect keyboard with resize listener, add `.keyboard-visible` class

```javascript
detectVirtualKeyboard() {
  let initialHeight = window.innerHeight;

  window.addEventListener('resize', () => {
    const currentHeight = window.innerHeight;
    const isKeyboardVisible = currentHeight < initialHeight * 0.8;

    if (isKeyboardVisible) {
      this.modal.classList.add('keyboard-visible');
    } else {
      this.modal.classList.remove('keyboard-visible');
      initialHeight = currentHeight;
    }
  });
}
```

**CSS Adjustment:**

```css
.modal.keyboard-visible .modal-content {
  max-height: 60vh;
}
```

---

## API Reference

### Constructor

```javascript
new GlassModal(element, options)
```

**Parameters:**

- `element` (String | HTMLElement) — Modal element or CSS selector
- `options` (Object) — Configuration options

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `keyboard` | Boolean | `true` | Allow Esc to close |
| `backdrop` | Boolean | `true` | Show backdrop |
| `focus` | Boolean | `true` | Auto-focus on open |
| `closeOnBackdrop` | Boolean | `true` | Close on backdrop click |
| `scrollable` | Boolean | `false` | Allow body scroll when open |
| `onShow` | Function | `null` | Callback before showing |
| `onShown` | Function | `null` | Callback after shown |
| `onHide` | Function | `null` | Callback before hiding |
| `onHidden` | Function | `null` | Callback after hidden |

### Instance Methods

#### `show()`

Open the modal.

```javascript
modal.show();
```

**Returns:** `void`

---

#### `hide()`

Close the modal.

```javascript
modal.hide();
```

**Returns:** `void`

---

#### `toggle()`

Toggle modal open/close state.

```javascript
modal.toggle();
```

**Returns:** `void`

---

#### `setContent(content)`

Update modal body content.

**Parameters:**

- `content` (String) — HTML content

```javascript
modal.setContent('<p>New content</p>');
```

**Returns:** `void`

---

#### `setTitle(title)`

Update modal title.

**Parameters:**

- `title` (String) — Title text

```javascript
modal.setTitle('Updated Title');
```

**Returns:** `void`

---

#### `destroy()`

Remove modal instance and cleanup.

```javascript
modal.destroy();
```

**Returns:** `void`

---

### Static Methods

#### `GlassModal.getInstance(element, options)`

Get existing instance or create new one.

**Parameters:**

- `element` (String | HTMLElement) — Modal element or selector
- `options` (Object) — Configuration options

```javascript
const modal = GlassModal.getInstance('#myModal');
```

**Returns:** `GlassModal` instance

---

#### `GlassModal.create(config)`

Create modal from configuration object.

**Parameters:**

- `config` (Object) — Modal configuration

**Config Options:**

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `id` | String | No | Modal ID (auto-generated if omitted) |
| `title` | String | No | Modal title (HTML allowed) |
| `body` | String | Yes | Modal body content (HTML) |
| `footer` | String | No | Modal footer content (HTML) |
| `size` | String | No | Size: `sm`, `lg`, `xl`, `fullscreen` |
| `type` | String | No | Type: `template`, `delete`, `preview`, `feedback` |
| `className` | String | No | Additional CSS class for `.modal-content` |
| ...options | * | No | Any option from constructor |

```javascript
const modal = GlassModal.create({
  id: 'dynamicModal',
  title: 'Dynamic Modal',
  body: '<p>Content here</p>',
  footer: '<button class="btn btn-primary">OK</button>',
  size: 'lg',
  type: 'template',
  onShown: () => console.log('Shown')
});
```

**Returns:** `GlassModal` instance

---

#### `GlassModal.confirm(config)`

Show confirmation dialog (Promise-based).

**Parameters:**

- `config` (Object) — Confirmation configuration

**Config Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | String | `"Confirm Action"` | Dialog title |
| `message` | String | `"Are you sure?"` | Confirmation message |
| `confirmText` | String | `"Confirm"` | Confirm button text |
| `cancelText` | String | `"Cancel"` | Cancel button text |
| `confirmClass` | String | `"btn-primary"` | Confirm button class |
| `icon` | String | `"bi-exclamation-triangle"` | Bootstrap icon class |

```javascript
const confirmed = await GlassModal.confirm({
  title: 'Delete Template',
  message: 'This action cannot be undone.',
  confirmText: 'Delete',
  confirmClass: 'btn-danger',
  icon: 'bi-trash'
});

if (confirmed) {
  // User clicked "Delete"
} else {
  // User clicked "Cancel" or closed modal
}
```

**Returns:** `Promise<boolean>`

---

#### `GlassModal.alert(config)`

Show alert dialog.

**Parameters:**

- `config` (Object) — Alert configuration

**Config Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | String | `"Alert"` | Dialog title |
| `message` | String | `""` | Alert message |
| `type` | String | `"info"` | Type: `success`, `warning`, `error`, `info` |
| `okText` | String | `"OK"` | OK button text |

```javascript
GlassModal.alert({
  title: 'Success',
  message: 'Template saved successfully!',
  type: 'success'
});
```

**Returns:** `void`

---

#### `GlassModal.hideAll()`

Close all open modals.

```javascript
GlassModal.hideAll();
```

**Returns:** `void`

---

## Known Edge Cases

### 1. Nested Modals

**Scenario:** Modal opened from within another modal

**Behavior:** Supported via modal stack

**Example:**

```javascript
// Open first modal
const modal1 = GlassModal.create({ title: 'Modal 1', body: '...' });
modal1.show();

// Open second modal
const modal2 = GlassModal.create({ title: 'Modal 2', body: '...' });
modal2.show();

// Stack: [modal1, modal2]
// Close modal2 → focus returns to modal1
```

**Limitation:** Max 3 nested modals recommended for UX

---

### 2. Browser Back Button

**Scenario:** User clicks browser back button while modal is open

**Behavior:** Modal remains open (no history entry)

**Workaround (future):** Use History API to add modal state

```javascript
// Future enhancement
modal.show();
history.pushState({ modalOpen: true }, '');

window.addEventListener('popstate', (e) => {
  if (!e.state.modalOpen) {
    modal.hide();
  }
});
```

---

### 3. Rapid Open/Close

**Scenario:** User rapidly clicks show/hide

**Behavior:** Debounced with transition duration (200ms)

**Protection:** `isOpen` flag prevents duplicate calls

---

### 4. Focus Loss

**Scenario:** Previously focused element removed from DOM

**Behavior:** Graceful fallback, no error

**Implementation:**

```javascript
if (this.previouslyFocusedElement && this.previouslyFocusedElement.focus) {
  this.previouslyFocusedElement.focus();
} else {
  document.body.focus();
}
```

---

### 5. SSR / No JavaScript

**Scenario:** Server-side rendering or JavaScript disabled

**Behavior:** Modals hidden, fallback to full-page navigation

**Progressive Enhancement:**

```html
<!-- Works without JS via href -->
<a href="/templates/create/" data-toggle="modal" data-target="#createModal">
  Create Template
</a>

<!-- JS enhances with modal -->
<script>
  document.querySelector('[data-toggle="modal"]').addEventListener('click', (e) => {
    e.preventDefault();
    const modal = GlassModal.getInstance('#createModal');
    modal.show();
  });
</script>
```

---

## Appendix

### Glassmorphic Design Tokens

```css
:root {
  /* Blur */
  --glass-blur: 25px;

  /* Opacity */
  --glass-opacity: 0.85;

  /* Border */
  --glass-border: 1px solid rgba(255, 255, 255, 0.18);

  /* Shadow */
  --glass-shadow: 0 20px 60px rgba(0, 43, 69, 0.3);

  /* Transition */
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-content {
  background: rgba(255, 255, 255, var(--glass-opacity));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: var(--glass-border);
  box-shadow: var(--glass-shadow);
  border-radius: var(--radius-2xl);
}
```

### Performance Checklist

- [x] Hardware-accelerated animations (transform, opacity)
- [x] Minimal DOM manipulation (classList over inline styles)
- [x] Event delegation where possible
- [x] Debounced event listeners
- [x] No memory leaks (cleanup in destroy())
- [x] Lazy creation (modals created on-demand)
- [x] CSS containment for reflow optimization

---

**End of Document**

For implementation examples, see:
- `/apps/mvp_ui/static/mvp_ui/js/modal-controller.js`
- `/apps/mvp_ui/static/mvp_ui/css/glass-modals.css`
- `/apps/mvp_ui/templates/mvp_ui/templates/list.html`
