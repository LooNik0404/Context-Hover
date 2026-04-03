"""Context Pad package root."""


def launch_context_pad():
    """Lazy import and launch manager window."""

    from .bootstrap import launch_context_pad as _launch

    return _launch()


def show_manager_window():
    """Lazy import and show manager window."""

    from .bootstrap import show_manager_window as _show

    return _show()


def show_script_launcher():
    """Lazy import and show script launcher."""

    from .bootstrap import show_script_launcher as _show

    return _show()


def show_set_launcher():
    """Lazy import and show set launcher."""

    from .bootstrap import show_set_launcher as _show

    return _show()


__all__ = ["launch_context_pad", "show_manager_window", "show_script_launcher", "show_set_launcher"]
