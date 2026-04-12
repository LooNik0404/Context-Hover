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


def hide_script_launcher():
    """Lazy import and hide script launcher unless pinned."""

    from .bootstrap import hide_script_launcher as _hide

    return _hide()


def hide_set_launcher():
    """Lazy import and hide set launcher unless pinned."""

    from .bootstrap import hide_set_launcher as _hide

    return _hide()


def show_set_launcher():
    """Lazy import and show set launcher."""

    from .bootstrap import show_set_launcher as _show

    return _show()


def install_startup():
    """Lazy import and run one-time install/setup flow."""

    from .bootstrap import install_startup as _install

    return _install()


def autostart():
    """Lazy import and run quiet startup initialization."""

    from .bootstrap import autostart as _autostart

    return _autostart()


def open_library_folder():
    """Lazy import and open active user library folder."""

    from .bootstrap import open_library_folder as _open

    return _open()


def get_library_folder_path():
    """Lazy import and return active library folder path."""

    from .bootstrap import get_library_folder_path as _get

    return _get()


def get_library_manifest_path():
    """Lazy import and return active manifest path."""

    from .bootstrap import get_library_manifest_path as _get

    return _get()


def print_paths():
    """Lazy import and print active Context Pad paths."""

    from .bootstrap import print_paths as _print

    return _print()


__all__ = [
    "launch_context_pad",
    "show_manager_window",
    "show_script_launcher",
    "hide_script_launcher",
    "show_set_launcher",
    "hide_set_launcher",
    "install_startup",
    "autostart",
    "open_library_folder",
    "get_library_folder_path",
    "get_library_manifest_path",
    "print_paths",
]
