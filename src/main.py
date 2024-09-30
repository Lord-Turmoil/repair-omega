import os
from arguments import parse_args
from prompt import CONSTRAINT, INITIAL_MESSAGE
from tools.lsp_integration import lsp_exit, lsp_init
from tools.gdb_integration import gdb_exit, gdb_init
from agent import agent_init

if __name__ == "__main__":
    args, profile, llm_config = parse_args()

    # Initialize GDB, LSP and the agent.
    gdb_init(profile["exec"], profile["args"], profile["env"], profile["cwd"])
    lsp_init(cwd=profile["src"])
    assistant, user_proxy = agent_init(llm_config)

    # Start the conversation.
    initial = INITIAL_MESSAGE
    if profile["constraint"]:
        initial += "\n" + CONSTRAINT.format(profile["constraint"])
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=initial,
    )

    # Terminate GDB and LSP.
    gdb_exit()
    lsp_exit()

    if args.keep:
        os.makedirs("log")
        os.system(f"cp log.log log/{profile['profile']}.log")
