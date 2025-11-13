import fm
import artifacts

safe_lim = 100
while safe_lim > 0:
    print(
f"""
{fm.BOLD}{fm.LIGHT_GREEN}Pacific Drive Artifacts CSV Generator{fm.CLEAR_ALL}
{fm.BOLD}1 ->{fm.CLEAR_ALL} Generate Artifacts CSV
{fm.BOLD}q ->{fm.CLEAR_ALL} Quit
""".strip())
    choice = input(f"> {fm.LIGHT_CYAN}").strip().lower()
    print(fm.CLEAR_ALL, end='')
    match choice:
        case '1':
            artifacts.run()
            input('Press Enter to quit...')
            exit(0)
        case 'q':
            exit(0)
        case _:
            print(f"{fm.LIGHT_RED}Invalid choice.{fm.CLEAR_ALL}")
    safe_lim -= 1
