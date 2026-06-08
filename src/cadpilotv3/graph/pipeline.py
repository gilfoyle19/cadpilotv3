from __future__ import annotations

from langgraph.graph import END, StateGraph

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.graph.routing import (
    route_contract_validation,
    route_critic_a,
    route_critic_b,
    route_repair,
    route_validation,
)


def build_pipeline(settings: AppSettings):
    graph = StateGraph(PipelineState)
    nodes = PipelineNodes(settings)

    _add_nodes(
        graph,
        intent_spec_agent=nodes.intent_spec_agent,
        geometry_planner_agent=nodes.geometry_planner_agent,
        critic_checkpoint_a=nodes.critic_checkpoint_a,
        parameter_agent=nodes.parameter_agent,
        code_generation_infill_agent=nodes.code_generation_infill_agent,
        execution_validation_node=nodes.execution_validation_node,
        contract_validation_node=nodes.contract_validation_node,
        repair_agent=nodes.repair_agent,
        critic_checkpoint_b=nodes.critic_checkpoint_b,
        export_summary_agent=nodes.export_summary_agent,
    )
    _wire_graph(graph)

    return graph.compile()


def build_async_pipeline(settings: AppSettings):
    graph = StateGraph(PipelineState)
    nodes = PipelineNodes(settings)

    _add_nodes(
        graph,
        intent_spec_agent=nodes.aintent_spec_agent,
        geometry_planner_agent=nodes.ageometry_planner_agent,
        critic_checkpoint_a=nodes.acritic_checkpoint_a,
        parameter_agent=nodes.aparameter_agent,
        code_generation_infill_agent=nodes.acode_generation_infill_agent,
        execution_validation_node=nodes.aexecution_validation_node,
        contract_validation_node=nodes.acontract_validation_node,
        repair_agent=nodes.arepair_agent,
        critic_checkpoint_b=nodes.acritic_checkpoint_b,
        export_summary_agent=nodes.aexport_summary_agent,
    )
    _wire_graph(graph)

    return graph.compile()


def _add_nodes(graph: StateGraph, **nodes) -> None:
    graph.add_node("intent_spec_agent", nodes["intent_spec_agent"])
    graph.add_node("geometry_planner_agent", nodes["geometry_planner_agent"])
    graph.add_node("critic_checkpoint_a", nodes["critic_checkpoint_a"])
    graph.add_node("parameter_agent", nodes["parameter_agent"])
    graph.add_node("code_generation_infill_agent", nodes["code_generation_infill_agent"])
    graph.add_node("execution_validation_node", nodes["execution_validation_node"])
    graph.add_node("contract_validation_node", nodes["contract_validation_node"])
    graph.add_node("repair_agent", nodes["repair_agent"])
    graph.add_node("critic_checkpoint_b", nodes["critic_checkpoint_b"])
    graph.add_node("export_summary_agent", nodes["export_summary_agent"])


def _wire_graph(graph: StateGraph) -> None:
    graph.set_entry_point("intent_spec_agent")

    graph.add_edge("intent_spec_agent", "geometry_planner_agent")
    graph.add_edge("geometry_planner_agent", "critic_checkpoint_a")

    graph.add_conditional_edges(
        "critic_checkpoint_a",
        route_critic_a,
        {
            "parameter_agent": "parameter_agent",
            "geometry_planner_agent": "geometry_planner_agent",
        },
    )

    graph.add_edge("parameter_agent", "code_generation_infill_agent")
    graph.add_edge("code_generation_infill_agent", "execution_validation_node")

    graph.add_conditional_edges(
        "execution_validation_node",
        route_validation,
        {
            "repair_agent": "repair_agent",
            "code_generation_infill_agent": "code_generation_infill_agent",
            "contract_validation_node": "contract_validation_node",
        },
    )

    graph.add_conditional_edges(
        "repair_agent",
        route_repair,
        {
            "execution_validation_node": "execution_validation_node",
            "code_generation_infill_agent": "code_generation_infill_agent",
            "geometry_planner_agent": "geometry_planner_agent",
            "contract_validation_node": "contract_validation_node",
        },
    )

    graph.add_conditional_edges(
        "contract_validation_node",
        route_contract_validation,
        {
            "critic_checkpoint_b": "critic_checkpoint_b",
            "export_summary_agent": "export_summary_agent",
        },
    )

    graph.add_conditional_edges(
        "critic_checkpoint_b",
        route_critic_b,
        {
            "export_summary_agent": "export_summary_agent",
            "code_generation_infill_agent": "code_generation_infill_agent",
            "geometry_planner_agent": "geometry_planner_agent",
        },
    )

    graph.add_edge("export_summary_agent", END)
