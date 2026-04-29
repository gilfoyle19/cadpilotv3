from cadpilotv3.prompts import compose_prompt, read_example_prompt, read_system_prompt


class PromptService:
    def get_system_prompt(self, name: str) -> str:
        return read_system_prompt(name)

    def get_example_prompt(self, name: str) -> str:
        return read_example_prompt(name)

    def build_prompt(self, system_name: str, example_name: str | None = None) -> str:
        return compose_prompt(system_name=system_name, example_name=example_name)