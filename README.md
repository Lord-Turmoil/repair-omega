# Repair Omega

---

## Quick Start

> Run `pip install -r requirements.txt` to install the required packages.

First, create a `config.yaml` under the root directory of the project. The content of the `config.yaml` should be like this:

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

Then, build the sample project under `sample`. Just run `make` under that directory. It will produce `main` binary.

Every run is configured by a profile under `profile.d`. See `sample.json` for example.

```json
{
    "cwd": "samples",           // working directory of the program to debug
    "exec": "samples/main",     // path to the binary to debug
    "src": "samples",           // path to the source code (for LSP to work)
    "args": [ "arg1", "arg2" ], // (optional) arguments to pass to the program
    "env": {                    // (optional) environment variables to set for the program
        "ENV1": "value1",
        "ENV2": "value2"
    }
}
```

Run `./run.sh sample` or just `./run.sh` under project root to analyze the sample project.

The result should be written to `location.txt`.

---

## Further Reading

By default, `./run.sh` will look for profile as you pass in the first argument. If the file is not found, it will look for it in `profile.d` directory next to it.

After running, it will generate `log.log` (function calling log) and `gdb.log` (GDB log) for debugging information.
