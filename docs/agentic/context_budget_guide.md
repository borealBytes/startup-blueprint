# Context Budget Management Guide

> How to work efficiently with limited context. Token management strategies for long conversations.

**Read this when**: Planning a large task or conversation getting long.  
**Don't read this**: Until you need context management strategies (saves context).

---

## Context Basics

### What is Context?

**Context = tokens available per thread** (~200,000 tokens)

Every message you send + every message I send uses tokens.

```
Available:     ~200,000 tokens
Base files:    ~4,000 tokens (instructions, autonomy_boundaries, workflow_guide)
Your task:     Variable
Conversation:  Grows with each message
Remaining:     What's left for code, analysis, output
```

### Token Usage Example

```
Your first message: "Build a dark mode toggle"
Tokens used: ~100 tokens

My response: ~500 tokens
Running total: ~600 tokens

Your follow-up: "Here's the code, review it"
Tokens: ~2,000 tokens (code is large)
Running total: ~2,600 tokens

My review: ~1,500 tokens
Running total: ~4,100 tokens

Available remaining: ~195,900 tokens ✅ Plenty of room
```

---

## Context Budget Allocation

### Recommended Distribution

For a typical task thread:

```
Base Instructions:           4,000 tokens (10%)
  - instructions.md
  - autonomy_boundaries.md
  - workflow_guide.md

Task Context:              10,000 tokens (20%)
  - Task description
  - Requirements
  - Background info

Working Context:          100,000 tokens (50%)
  - File contents
  - Code snippets
  - Analysis
  - Explanations

Buffer/Safety:             86,000 tokens (20%)
  - Don't use this
  - Keep it free
  - For unexpected needs

Total:                    200,000 tokens (100%)
```

### Real-World Allocation

**Simple task** (bug fix):
```
Base:     4,000
Task:     2,000
Working: 20,000
Buffer:  174,000 ← Tons of room
```

**Complex task** (refactor):
```
Base:     4,000
Task:    10,000
Working: 100,000
Buffer:  86,000 ← Still safe
```

**Very complex task** (architecture):
```
Base:     4,000
Task:    20,000
Working: 150,000
Buffer:  26,000 ← Getting tight, consider new thread
```

---

## When to Create New Thread

### Signs You Should Create New Thread

✅ **Create new thread when**:
- Context usage > 70% (140K tokens)
- Conversation has 50+ messages
- Task changes significantly
- You've been working > 2 hours
- Conversation history getting long
- Work feels slow (agent struggling)

❌ **Don't create new thread**:
- You have < 5 messages
- Task is almost done
- Context usage < 50%
- Working smoothly

### Creating New Thread (Checklist)

When context is getting full:

```
1. ✅ Save current work
   - Push code to GitHub
   - Commit in progress work
   - Note where you left off

2. ✅ Write summary for new thread
   "Task: Implement dark mode
   Progress: 70% complete
   - Button created
   - Styles working
   - Testing next
   Files changed: src/components/DarkMode.tsx
   Current branch: feat/dark-mode"

3. ✅ Create new thread
   - Copy the summary above
   - Paste as first message
   - Continue work from there

4. ✅ Reference old thread if needed
   "Earlier in a different thread, we decided..."
```

---

## Context-Efficient Workflows

### Strategy 1: Reference Files By Name

❌ **Bad** (uses lots of context):
```
You: "Here's the Button component I want to fix:

[Pastes entire 500-line Button.tsx file]

Can you add a new prop?"

Context used: ~2,000 tokens
```

✅ **Good** (saves context):
```
You: "Fix the Button component (src/components/Button.tsx).
Add a 'disabled' prop that greys out the button."

Context used: ~50 tokens

Me: "I can see Button.tsx in the repo. Here's what I'll do:
[Small code snippet showing the change]"
```

### Strategy 2: Ask for Specific Sections

❌ **Bad**:
```
You: "Review the entire codebase and find performance issues."
Context used: ~50,000 tokens (entire repo loaded)
```

✅ **Good**:
```
You: "Review the database query in
QueryBuilder.ts (lines 45-60) for performance issues."
Context used: ~500 tokens (specific section)
```

### Strategy 3: Keep Tasks Focused

❌ **Bad** (multiple tasks):
```
"Build dark mode, add animations, refactor DB, optimize images"
Context used: Explodes because each task needs full context
```

✅ **Good** (single focus):
```
"Build dark mode toggle. That's it.
Animations and refactoring in separate threads."
Context used: ~40% of budget
```

### Strategy 4: Summarize Frequently

❌ **Bad** (scroll through history):
```
Thread has 100 messages. Need to reference decision from message 15.
Context used: Need to load all 100 messages to find it.
```

✅ **Good** (save summaries):
```
Every 20 messages: "Summary so far:
- Decided to use React for UI
- Database is PostgreSQL
- Styling with Tailwind"
Context used: Cleaner history, easier to reference
```

---

## File Reference Guide

### How to Reference Files Efficiently

```
✅ GOOD: "Fix the bug in src/utils/helpers.ts, line 45"
❌ BAD:  "Here's the entire helpers.ts file [pastes 5KB]"

✅ GOOD: "Update the Button component's onClick handler"
❌ BAD:  "Here's Button.tsx, PageHeader.tsx, Footer.tsx [pastes 10KB]"

✅ GOOD: "Check the database schema for the users table"
❌ BAD:  "Here's the entire schema.sql file [pastes 20KB]"
```

### Reference Shorthand

```
Instead of:              Use this shorthand:
────────────────────────────────────────────────────────────
"In src/components      "In Button.tsx
Button.tsx, line 45"    (line 45)"

"In the entire          "In the User model
models/User.ts file"    (see models/User.ts)"

"In src/pages/index     "In the home page
within the Component"   (pages/index.tsx)"
```

---

## Conversation Pacing

### Fast Pace (More Context)

```
Thread: 10 messages, 50K tokens
Pacing: 5K tokens per message
Length: 2 hours
Risk: Getting full

Solution: Summarize or create new thread
```

### Slow Pace (Less Context)

```
Thread: 50 messages, 50K tokens  
Pacing: 1K tokens per message
Length: 5 hours
Risk: Low, you can keep going

Solution: Continue in same thread
```

### Typical Pace (Comfortable)

```
Thread: 20 messages, 60K tokens
Pacing: 3K tokens per message
Length: 1-2 hours
Risk: Moderate

Solution: Monitor and create new thread at 70%
```

---

## Large File Handling

### Scenario: Editing a Large File

```
File: components/ComplexForm.tsx (3,000 lines)
Task: Add a new field to the form

❌ WRONG:
You: "Here's the entire ComplexForm.tsx"
[Pastes entire 3,000 lines = 5K tokens]

✅ RIGHT:
You: "In ComplexForm.tsx, the renderFields() function
(lines 500-650) needs a new email field.

Current structure:
- Name field at line 550
- Email field should go after it
- Validation follows same pattern

Can you implement it?"
[~200 tokens of description instead]
```

### Scenario: Multiple File Changes

```
Changes needed in:
- src/components/Form.tsx
- src/utils/validation.ts
- src/pages/settings.tsx

❌ WRONG:
You: "Update all these files"
[Pastes entire content = 10K tokens]

✅ RIGHT:
You: "Update these three files:
1. Form.tsx: Add submit button (around line 200)
2. validation.ts: Add email validation (after line 100)
3. settings.tsx: Update import (line 5)

Here's the exact changes needed:
- Form: Add <button>Submit</button>
- Validation: export function validateEmail()
- Settings: import { validateEmail }

Can you implement?"
[~500 tokens instead of 10K]
```

---

## Monitoring Context Usage

### Visual Indicators

**Watch for these signs**:

```
Context at 50% (100K tokens used)
✅ Safe, continue normally

Context at 70% (140K tokens used)  
⚠️ Getting full, start wrapping up

Context at 85% (170K tokens used)
🔴 Very full, create new thread NOW
```

### How to Check

I'll tell you if context is getting full.

Or you can estimate:
- Simple conversation: ~1K tokens per message
- With code: ~2-5K tokens per message
- With large files: ~5-10K tokens per message

---

## Best Practices

### ✅ DO

- ✅ Reference files by name instead of pasting
- ✅ Ask for specific code sections
- ✅ Keep tasks focused and narrow
- ✅ Create new thread when > 70% full
- ✅ Summarize frequently (every 20 messages)
- ✅ Push code regularly (don't lose work)
- ✅ Write clear task descriptions upfront

### ❌ DON'T

- ❌ Paste entire files into chat
- ❌ Ask for analysis of whole codebase
- ❌ Try multiple tasks in one thread
- ❌ Keep conversation going past 80% full
- ❌ Re-explain the same thing repeatedly
- ❌ Leave code uncommitted
- ❌ Use vague descriptions

---

## Quick Decision Tree

```
Starting new task
    |
    ├─ Simple (< 1 hour)?
    │  └─ Same thread, no worries
    │
    ├─ Complex (1-3 hours)?
    │  └─ Same thread, monitor usage
    │
    └─ Very complex (> 3 hours)?
       └─ Plan for new thread at 70%

In middle of task
    |
    ├─ < 50% context used?
    │  └─ Continue, lots of room
    │
    ├─ 50-70% used?
    │  └─ Monitor, wrap up soon
    │
    └─ > 70% used?
       └─ Create new thread now
```

---

## Summary

**Context = token budget per thread**

- You have ~200K tokens
- Use ~4K for base files
- Use ~10-100K for your task
- Keep 20-30K as buffer

**To use context efficiently**:
1. Reference files by name (don't paste)
2. Ask for specific sections (not whole files)
3. Keep tasks focused (one per thread)
4. Create new thread when > 70% full
5. Summarize periodically

**When in doubt**: Create new thread and continue. It's free, and you get fresh context.
