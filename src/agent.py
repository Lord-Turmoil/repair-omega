from autogen import ConversableAgent, register_function
from consts import CO_OUTPUT, PATCH_OUTPUT
from prompt import (
    CO_SYSTEM,
    FL_SYSTEM_DBG,
    FL_SYSTEM_NO_DBG,
    PG_SYSTEM,
)
from functions import (
    confirm_location,
    confirm_patch,
    definition,
    function_body,
    get_file_content,
    print_value,
    run_program,
    run_to_line,
    set_expected_function,
    set_patch_output,
    set_run_mode,
    summary,
    switch_frame,
)


def agent_init_fl(llm_config, profile):
    system_message = FL_SYSTEM_DBG if profile["debug"] else FL_SYSTEM_NO_DBG

    # Initialize LLM agent and user proxy.
    assistant = ConversableAgent(
        name="Crosshair", system_message=system_message, llm_config=llm_config
    )
    user_proxy = ConversableAgent(
        name="Fix Localization Toolset",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None
        and "TERMINATE" in msg["content"],
        human_input_mode="TERMINATE",
    )

    set_run_mode(profile["mode"])
    set_expected_function(profile["function"])

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

    # for now, force debug mode
    assert profile["debug"]

    if profile["debug"]:
        register_function(
            print_value,
            caller=assistant,
            executor=user_proxy,
            description="Print the value of an expression in the current context",
        )
        # register_function(
        #     switch_frame,
        #     caller=assistant,
        #     executor=user_proxy,
        #     description="Switch to a different stack frame in the backtrace",
        # )
        register_function(
            run_to_line,
            caller=assistant,
            executor=user_proxy,
            description="Run the program in GDB until the specified line",
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
        confirm_location,
        caller=assistant,
        executor=user_proxy,
        description="Confirm the fix locations in the code",
    )

    return assistant, user_proxy, system_message


def agent_init_pg(llm_config, profile):
    system_message = PG_SYSTEM

    # Initialize LLM agent and user proxy.
    assistant = ConversableAgent(
        name="Tech", system_message=system_message, llm_config=llm_config
    )
    user_proxy = ConversableAgent(
        name="Patch Generation Toolset",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None
        and "TERMINATE" in msg["content"],
        human_input_mode="TERMINATE",
    )

    set_run_mode(profile["mode"])
    set_patch_output(PATCH_OUTPUT)

    # Register functions.
    register_function(
        get_file_content,
        caller=assistant,
        executor=user_proxy,
        description="Get the content of the given file from start line to end line",
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
        confirm_patch,
        caller=assistant,
        executor=user_proxy,
        description="Confirm the patch for the fix location",
    )

    return assistant, user_proxy, system_message


def agent_init_co(llm_config, profile):
    system_message = CO_SYSTEM

    # Initialize LLM agent and user proxy.
    assistant = ConversableAgent(
        name="Echo", system_message=system_message, llm_config=llm_config
    )
    user_proxy = ConversableAgent(
        name="Chat Only Toolset",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None
        and "TERMINATE" in msg["content"],
        human_input_mode="TERMINATE",
    )

    set_run_mode(profile["mode"])
    set_patch_output(CO_OUTPUT)

    # Register functions.
    register_function(
        confirm_patch,
        caller=assistant,
        executor=user_proxy,
        description="Confirm the patch for the fix location",
    )

    return assistant, user_proxy, system_message
