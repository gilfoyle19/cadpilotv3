from cadpilotv3.prompts import compose_prompt, read_system_prompt
from cadpilotv3.services.prompt_service import PromptService


def main() -> None:
    print("=== system prompt ===")
    print(read_system_prompt("intent_spec_agent"))

    print("\n=== composed prompt ===")
    print(compose_prompt("intent_spec_agent", "intent_spec_examples"))

    service = PromptService()
    print("\n=== service prompt ===")
    print(service.build_prompt("geometry_planner_agent", "geometry_planner_examples"))


if __name__ == "__main__":
    main()