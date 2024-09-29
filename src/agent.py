from autogen import ConversableAgent, register_function
from prompt import SYSTEM_MESSAGE
from functions import (
    confirm,
    definition,
    function_body,
    get_file_content,
    print_value,
    run_program,
    summary,
    switch_frame,
)


def agent_init(llm_config):
    # Initialize LLM agent and user proxy.
    assistant = ConversableAgent(
        name="Crosshair", system_message=SYSTEM_MESSAGE, llm_config=llm_config
    )
    user_proxy = ConversableAgent(
        name="Toolset",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None
        and "TERMINATE" in msg["content"],
        human_input_mode="TERMINATE",
    )

    # Register functions.
    register_function(
        get_file_content,
        caller=assistant,
        executor=user_proxy,
        description="Get the content of the given file from start line to end line",
    )

    register_function(
        run_program,
        caller=assistant,
        executor=user_proxy,
        description="Start debugging the given program in GDB and get the backtrace",
    )
    register_function(
        print_value,
        caller=assistant,
        executor=user_proxy,
        description="Print the value of an expression in the current context",
    )
    register_function(
        switch_frame,
        caller=assistant,
        executor=user_proxy,
        description="Switch to a different stack frame in the backtrace",
    )

    register_function(
        definition,
        caller=assistant,
        executor=user_proxy,
        description="Get the definition of a symbol at a given position",
    )
    register_function(
        summary,
        caller=assistant,
        executor=user_proxy,
        description="Get the summary information of a symbol at a given position",
    )
    register_function(
        function_body,
        caller=assistant,
        executor=user_proxy,
        description="Get the body of the function in the given file",
    )

    register_function(
        confirm,
        caller=assistant,
        executor=user_proxy,
        description="Confirm the fix locations in the code",
    )

    return assistant, user_proxy
