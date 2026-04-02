# Context Pad Command Execution Stage

## Public API

```python
from context_pad.core.command_runner import run_button_action

ok = run_button_action(button_data)
```

- `run_button_action(button_data: dict) -> bool`
- Supports command types:
  - `python_inline`
  - `python_file`
  - `mel_inline`
  - `mel_file`

## Example `button_data` payloads (all 4 command types)

```python
PYTHON_INLINE = {
    "label": "Py Inline Hello",
    "type": "python_inline",
    "code": 'print("Hello from python_inline")',
}

PYTHON_FILE = {
    "label": "Py File Action",
    "type": "python_file",
    "file_path": r"C:/temp/context_pad/my_action.py",
}

MEL_INLINE = {
    "label": "MEL Inline Hello",
    "type": "mel_inline",
    "code": 'print "Hello from mel_inline\\n";',
}

MEL_FILE = {
    "label": "MEL File Action",
    "type": "mel_file",
    "file_path": r"C:/temp/context_pad/my_action.mel",
}
```

## Test cases

### Positive (4)
- `python_inline`: simple print line.
- `python_file`: run existing `.py` file.
- `mel_inline`: simple MEL print.
- `mel_file`: run existing `.mel` file.

### Negative (2)
- Missing file path target.
- Intentionally broken inline python code.

Use built-in temporary harness:

```python
from context_pad.core.command_runner_harness import run_demo_execution_tests
print(run_demo_execution_tests())
```

## Minimal connection to existing launcher (temporary)

```python
from context_pad.bootstrap import show_script_launcher
from context_pad.core.command_runner import run_button_action

launcher = show_script_launcher()

# Temporary wiring for test: execute payload if button dict includes type/code/file_path
launcher._command_grid.button_clicked.connect(run_button_action)
```

## Maya Script Editor snippets

### Run successful Python action

```python
from context_pad.core.command_runner import run_button_action
run_button_action({
    "label": "Py Inline Success",
    "type": "python_inline",
    "code": 'print("Python action success")',
})
```

### Run successful MEL action

```python
from context_pad.core.command_runner import run_button_action
run_button_action({
    "label": "MEL Inline Success",
    "type": "mel_inline",
    "code": 'print "MEL action success\\n";',
})
```

### Run failing action

```python
from context_pad.core.command_runner import run_button_action
run_button_action({
    "label": "Broken Action",
    "type": "python_inline",
    "code": "for i in range(3) print(i)",
})
```

## Manual validation checklist

1. Successful Python command runs and returns `True`.
2. Successful MEL command runs and returns `True`.
3. Missing file action returns `False` with readable warning.
4. Broken inline code returns `False` with readable error.
5. UI remains decoupled: execution logic lives in `core/command_runner.py`.

## Expected result

- Supported actions execute correctly when payload is valid.
- Failures are safe and readable in Script Editor.
- Missing files never crash launcher code.
- UI can call execution through one function (`run_button_action`) without knowing internals.

## Known limitations of this stage

- No manifest loading yet; payloads are direct dictionaries.
- No permission/sandbox layer for external scripts.
- No undo chunk management around actions yet.
- No async execution queue.
