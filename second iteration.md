# PromptCraft v0.5 – Production Requirements Specification

## 🚀 Goal
Deliver a lightweight, production-ready version of PromptCraft that fetches prompt templates from the backend and displays them in a polished UI. This version will be used to publicly launch and validate the core experience.

---

## 📦 Version
- **App Name**: PromptCraft
- **Version**: 0.5 (Production MVP)
- **Platform**: Flutter (Frontend) + Custom Backend (by owner)
- **Build Target**: Android / iOS / Web (Optional)

---

## 🧩 Core Features (v0.5 Scope)
| Feature | Description |
|--------|-------------|
| 🔄 Backend Integration | Fetch curated prompts via REST API (`GET /prompts`) |
| 🗂 Prompt Listing UI | Display all fetched prompt templates in scrollable cards |
| 🔍 Search & Filter | Optional: Simple search bar to filter prompts by title or tag |
| 📄 Prompt Viewer | View full prompt with metadata (tags, description) |
| 📥 One-Click Copy | Copy prompt to clipboard for quick use |
| 📱 Lightweight Build | Minimize app size by excluding heavy assets, use lazy loading |

---

## 🔌 Backend API Integration
Assumes backend provides:
- `GET /api/prompts/` → Returns list of prompts (paginated)
- JSON Format:
```json
[
  {
    "id": 1,
    "title": "Build a SaaS App from a Prompt",
    "prompt": "You are a senior engineer. Build a SaaS web app based on: {Build a journaling tracker app}",
    "tags": ["#software", "#engineering", "#app"],
    "category": "Software",
    "use_case": "App Generator"
  },
  ...
]
