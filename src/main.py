from arguments import parse_args
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
    chat_result = user_proxy.initiate_chat(
        assistant,
        message=f"Use the functions provided to analyze the crash in the program and give possible fix locations.",
    )

    # Terminate GDB and LSP.
    gdb_exit()
    lsp_exit()
