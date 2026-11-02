import builtins

from colorama import Fore, Style, init


_original_print = builtins.print


def get_color(line):
    text = line.strip().upper()

    if not text:
        return ""

    # Leave manually formatted ANSI output unchanged.
    if "\x1b[" in line:
        return ""

    # Feasible trajectory headings should be white.
    if "FEASIBLE TRAJECTORY" in text:
        return Fore.WHITE

    # Frame information should be white.
    if text.startswith("FRAME "):
        return Fore.WHITE

    # Victory messages.
    if "CREWMATES WIN" in text:
        return Fore.GREEN + Style.BRIGHT

    if "IMPOSTORS WIN" in text:
        return Fore.RED + Style.BRIGHT

    # Ejections.
    if "WAS EJECTED" in text:
        return Fore.RED + Style.BRIGHT

    # Kills and body discoveries.
    if (
        "ELIMINATED" in text
        or "DISCOVERED" in text
    ):
        return Fore.RED + Style.BRIGHT

    # Section headings.
    if (
        text.startswith("===")
        or text.startswith("---")
        or text.startswith("=" * 10)
    ):
        return Fore.CYAN + Style.BRIGHT

    # Roles.
    if "IMPOSTOR" in text:
        return Fore.MAGENTA

    if "CREWMATE" in text:
        return Fore.BLUE

    # Voting information is white.
    if "VOTE" in text or "TIE BETWEEN" in text:
        return Fore.WHITE

    # Errors and warnings.
    if (
        "FAILED" in text
        or "INCONSISTENT" in text
        or "NO POSSIBLE" in text
    ):
        return Fore.RED

    return Fore.WHITE


def colored_print(*values, sep=" ", end="\n", file=None, flush=False):
    message = sep.join(str(value) for value in values)

    colored_lines = []

    for line in message.split("\n"):
        color = get_color(line)

        if color:
            colored_lines.append(
                f"{color}{line}{Style.RESET_ALL}"
            )
        else:
            colored_lines.append(line)

    _original_print(
        "\n".join(colored_lines),
        end=end,
        file=file,
        flush=flush
    )


def install_colorama():
    # Enable ANSI colour support in the terminal.
    init(autoreset=True)

    # Apply colour formatting to print statements throughout the project.
    builtins.print = colored_print