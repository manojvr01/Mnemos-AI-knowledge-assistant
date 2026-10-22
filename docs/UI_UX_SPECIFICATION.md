# UI/UX Specification — Mnemos

**Document Reference:** UI-MNEMOS-1.0  
**Design Reference:** [milestone_a_design_specification.md](file:///c:/Users/manoj/.gemini/antigravity-ide/brain/42b18ee6-b7e1-4ac4-945f-81b7e266fbec/milestone_a_design_specification.md)  
**Related Documents:** [PRD.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/PRD.md), [ARCHITECTURE.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/ARCHITECTURE.md)

---

## 1. Visual Paradigm & Design Direction

Mnemos is styled as a professional, paid enterprise command center. It rejects toy-like consumer chatbots, excessive glassmorphism, and neon eye strain in favor of a dark obsidian canvas, surgical hairline borders, high typography contrast, and restrained violet/indigo accents.

### Core Design Principles
1. **Evidence-First Layout:** Citations are not footnotes or afterthoughts; they are first-class interactive pills embedded directly alongside claims.
2. **Deterministic Layout Stability:** Tabular numbers (`tnum`) and fixed-width containers prevent horizontal shifts during message generation and document indexing.
3. **Multi-Pane Context Workstation:** The screen is divided into dedicated functional zones: Navigation Rail, Central Interaction Canvas, and Contextual Source Inspector.

---

## 2. Design Tokens

```css
:root {
  /* Surface Layers */
  --bg-canvas: #0B0F19;         /* Floor canvas */
  --bg-sidebar: #080C18;        /* Receded navigation anchor */
  --bg-surface: #111827;        /* Cards and primary modules */
  --bg-surface-elevated: #161D32; /* Modals, popovers, source drawer */
  
  /* Hairline Borders */
  --border-subtle: #1F2937;     /* rgba(255, 255, 255, 0.08) */
  --border-hover: #374151;      /* rgba(255, 255, 255, 0.16) */
  --border-focus: #6366F1;      /* Violet active focus */

  /* Text & Foreground */
  --text-primary: #F9FAFB;      /* Contrast ratio > 13:1 */
  --text-secondary: #9CA3AF;    /* Metadata, timestamps */
  --text-muted: #6B7280;        /* Inactive labels */

  /* Semantic Accents */
  --accent-primary: #6366F1;    /* Restrained Violet */
  --accent-primary-hover: #4F46E5; /* Deep Indigo */
  --accent-highlight: #3B82F6;  /* Electric Blue (Source excerpts) */
  --status-indexed: #10B981;    /* Emerald green */
  --status-processing: #38BDF8; /* Sky blue */
  --status-warning: #F59E0B;    /* Amber */
  --status-error: #EF4444;      /* Rose red */

  /* Radii */
  --radius-card: 12px;
  --radius-control: 8px;
  --radius-pill: 9999px;
  --radius-badge: 6px;
}
```

---

## 3. Screen Specifications

### 3.1 Knowledge Dashboard (`/dashboard`)
- **Header:** Global semantic search bar (`Cmd+K`) and `"Ask a Question"` CTA button in primary gradient (`linear-gradient(135deg, #6366F1 0%, #3B82F6 100%)`).
- **Quick Upload Zone:** Drag-and-drop target accepting `.pdf`, `.docx`, `.txt` up to 50MB. Shows instant upload progress bar.
- **Metrics Grid:** Real computed numbers: Documents Indexed, Knowledge Chunks, Verified Queries.
- **Documents Table:**
  - Status badges with icon + text (e.g., green dot + "Indexed", blue pulsing dot + "Processing", red alert + "Failed").
  - Columns: Filename, Status, Pages, Size, Upload Date, Quick Actions (View, Delete).
- **Recent Research Sessions:** Clickable cards opening past conversation threads.

### 3.2 AI Chat & Evidence Workspace (`/chat`)
- **Left Column (260px):** Recent conversations list with "New Thread" button, rename, and delete actions.
- **Center Stage:**
  - Message bubble stream.
  - **Assistant Message Card:**
    - Explicit section **Synthesis** (executive overview).
    - Explicit section **Grounding Evidence** (bullet points with exact claims).
    - **Citation Pills:** Interactive pills `[1] Q3_Financial_Report.pdf p.14`. Hover shows tooltip with excerpt; click opens Source Inspector Drawer.
  - **Composer:** Input field, Scope selector dropdown (`All Documents` vs `Collection`), Suggested follow-up prompt pills, and Send button.
- **Right Column (Source Inspector Drawer - 380px):**
  - Slides out smoothly when citation is clicked.
  - Displays Document title, Exact page number (or note: *"Unpaginated document format"*), Similarity score badge (`94% Match`).
  - Passage excerpt card with matching key phrases highlighted in electric blue (`#3B82F6`).

---

## 4. Accessibility & States

1. **Color Independence:** Status is never communicated by color alone; every indicator includes a text label and distinctive icon.
2. **Focus Visibility:** Standard `focus-visible:ring-2 focus-visible:ring-indigo-500` applied to all keyboard-interactive elements.
3. **Screen Readers:** ARIA labels on all icon-only buttons, modal drawers, and progress bars.
4. **Empty States:** Clear illustrations and action-oriented messaging for empty document libraries and new chat sessions.
