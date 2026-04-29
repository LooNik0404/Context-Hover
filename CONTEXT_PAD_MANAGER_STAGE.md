# Context Pad Manager — Simplified Workflow

## Open manager window (Maya Script Editor, Python tab)

```python
from context_pad.bootstrap import launch_context_pad
launch_context_pad()
```

## New workflow overview

The manager now focuses on **script buttons** and is split into 2 tabs:

1. **Button Setup**
   - Categories (left)
   - Buttons for selected category (middle)
   - Basic button properties only (right):
     - Button Name
     - Category
     - Color

2. **Code Editor**
   - Edits the **same currently selected button** from Button Setup
   - Shows current selection as `Category > Button`
   - Language: Python / MEL
   - One large code editor
   - Tooltip field
   - Actions: Apply / Save Library / Reload Library

Scene set operations stay primarily in the Set Launcher hover workflow.

## Manual validation checklist

- I can create a category.
- I can create a button.
- I can rename and reorder categories/buttons.
- I can select a button in Button Setup.
- Code Editor edits that same selected button.
- I can switch Python / MEL.
- I can edit code directly.
- I do not see source mode/file path controls in the manager UI.
- The manager feels cleaner and easier to understand.
