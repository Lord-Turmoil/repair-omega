# Repair Omega

---

## Quick Start

> Run `pip install -r requirements.txt` to install the required packages.

First, create a `config.yaml` under the root directory of the project. The content of the `config.yaml` should be like this, which contains the configuration of the LLM service.

```yaml
llm:
  select: openai
  profiles:
    - name: qianwen
      base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
      api_key: sk-***
      model: qwen-turbo
    - name: openai
      base_url: https://agi.ylsap.com/tolinks/v1
      api_key: Token-***
      model: gpt-4-turbo
```

Every run is configured by a profile under `profile.d`. See `sample.json` for example.

```json
{
    "project": "sample", // path of the project
    "build": [ "make" ], // build command
    "run": "main",       // relative path to the binary (after build) to the project root
    "args": [ "arg1", "arg2" ], // (optional) arguments to pass to the program
    "env": {                    // (optional) environment variables to set for the program
        "ENV1": "value1",
        "ENV2": "value2"
    },
    "mode": "gdb",  // (optional) run program with gdb or sanitizer (default is "gdb")
    "init": "init", // (optional) path to the test case directory (default is None)
    "sandbox": "",  // (optional) path to the sandbox directory (defualt is .sandbox)
    "work": "",     // (optional) path to the working directory (default is .work)
    "output": "",   // (optional) path to the output file (default is "locations.txt")
    "constraint": "(And (Slt s spp) (Slt s 8))", // constraint for the fix location
    "function": "sum" // crashed function name
}
```

Use the wrapper script `./run.sh` to run fix localization. If its your first run, you should specify `-d` to perform a dry run, other wise you can omit `-d` to use the modified source code in the sandbox. If you want to keep the logs, you can specify `-k` and logs will be output to `log/` directory with a subdirectory and several files `<project>-<model>[-c]/<type>.log` (`-c` means whether there is constraint).

```bash
./run.sh -d -k
```

---

## Further Reading

### Configuration

By default, the program will look for the given profile with exact path and name, and if not found, it will look for it in `profile.d` directory next to it. You can specify the profile name with `-p` option.

```bash
./run.sh -d -k -p profile
```

For the `project` field, you can specify either absolute path or relative path to the current working directory. It is recommended to run the program under the root directory of the project using `run.sh`.

### Log

After running, it will generate three log files:

- `log.log`: main program log
- `function.log`: function calling log
- `gdb.log`: GDB log

Previous log will be overwritten if you run the script again. To persist the log, you can specify `-k` to keep the log, so that `function.log` and `log.log` will be persisted to `log/` directory with `<type>` of `function` and `log` respectively.

### Workflow

1. If dry run specified, will copy the project to sandbox. (Previous sandbox will be removed.)
2. Build the project with the specified build command.
3. If `init` specified, will copy all files **under** the directory to the working directory. (Previous working directory will be removed.)
4. Debug the project with the specified binary, arguments and environment under the working directory.
5. If the program crashes, will try to fix the localization and output fix location to output file.

### Batch Run

There are currently many options to run on a project, they are:

- constraint + debug
- debug only
- constraint only
- nothing

To run these "presets" at once, you can use the `batch_run.sh`. To use it, prepare two profiles: `<profile>` (no constraint) and `<profile>-c` (with constraint), and run the following command:

```bash
./batch_run.sh -p <profile>
```

It will run all the presets automatically.

### Note

If the build command is complex, e.g. including multiple commands, you can write a shell script to wrap it and specify the script as the build command.

```json
{
    // ...
    "build": [
        "bash",
        "build.sh"
    ],
    // ...
}
```
