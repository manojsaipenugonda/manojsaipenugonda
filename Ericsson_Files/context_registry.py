"""
Context Registry — Anti-Hallucination Enforcement Layer
═══════════════════════════════════════════════════════════
Maps each intent_type to its context constraints:
  - allowed_tables: whitelist of tables the agent MAY query
  - forbidden_tables: tables the agent MUST NOT query
  - anti_hallucination: rules injected into agent prompts
  - primary_agent: which agent handles this intent
  - output_contract: expected response format

This is the RUNTIME equivalent of the question bank's agent_context field.
Called by callbacks.py to enforce constraints before/after agent execution.
"""

from typing import Optional

# =============================================================================
# ALL NPS ENHANCEMENT TABLES
# =============================================================================

ALL_TABLES = [
    "nps_enhancement_sites",
    "nps_enhancement_nps",
    "nps_enhancement_ran_daily_trend",
    "nps_enhancement_ran_daily_anomalies",
    "nps_enhancement_alarms",
    "nps_enhancement_battery",
    "nps_enhancement_black_cells",
    "nps_enhancement_open_tickets",
    "nps_enhancement_closed_tickets",
    "nps_enhancement_weekly_chronic_down",
    "nps_enhancement_weekly_churn",
    "nps_enhancement_complaint_analysis",
    "nps_enhancement_topology",
    "nps_enhancement_forecast_nps",
    "nps_enhancements_auto_tt_dual_cut_path_cache",
    "nps_enhancements_auto_tt_dual_cut_path_cache_true",
    "nps_enhancements_auto_tt_dual_cut_risk_cache",
    "nps_enhancements_auto_tt_dual_cut_risk_cache_true",
    "nps_enhancements_auto_tt_dual_cut_spof_cache",
    "nps_enhancements_auto_tt_dual_cut_spof_cache_true",
]


def _forbidden_from_allowed(allowed: list[str]) -> list[str]:
    """Compute forbidden tables as ALL minus allowed."""
    allowed_set = set(allowed)
    return sorted(t for t in ALL_TABLES if t not in allowed_set)


# =============================================================================
# INTENT CONTEXT REGISTRY
# =============================================================================

INTENT_REGISTRY = {
    # ─── Simple Retrieval Intents ───────────────────────────────────────────
    "availability": {
        "primary_agent": "availability_agent",
        "allowed_tables": [
            "nps_enhancement_ran_daily_trend",
            "nps_enhancement_ran_daily_anomalies",
        ],
        "anti_hallucination": [
            "Do NOT include NPS score data",
            "Do NOT query alarm or ticket tables",
            "Do NOT broaden to other sites unless explicitly asked",
            "Focus ONLY on RAN KPI metrics from ran_daily_trend and ran_daily_anomalies",
        ],
        "output_format": "table",
    },
    "alarm": {
        "primary_agent": "alarm_agent",
        "allowed_tables": ["nps_enhancement_alarms"],
        "anti_hallucination": [
            "Do NOT include NPS or KPI data",
            "Do NOT query availability tables",
            "Do NOT fabricate alarm descriptions not present in the data",
            "Report ONLY alarm records from the alarms table",
        ],
        "output_format": "table",
    },
    "ticket": {
        "primary_agent": "ticket_agent",
        "allowed_tables": [
            "nps_enhancement_open_tickets",
            "nps_enhancement_closed_tickets",
        ],
        "anti_hallucination": [
            "Do NOT include alarm or KPI data",
            "Do NOT conflate open and closed ticket counts",
            "Do NOT invent ticket descriptions not in the data",
        ],
        "output_format": "table",
    },
    "nps": {
        "primary_agent": "customer_experience_agent",
        "allowed_tables": ["nps_enhancement_nps"],
        "anti_hallucination": [
            "Do NOT include RAN KPI data",
            "Do NOT query alarm or ticket tables",
            "Report ONLY NPS metrics from the nps table",
            "ALWAYS use DISTINCT ON (date) when querying nps_enhancement_nps — this table has multiple rows per date per site",
        ],
        "output_format": "table",
    },
    "power": {
        "primary_agent": "power_agent",
        "allowed_tables": ["nps_enhancement_battery"],
        "anti_hallucination": [
            "Do NOT include alarm or KPI data",
            "Do NOT query availability tables",
            "Report ONLY power/battery events from the battery table",
        ],
        "output_format": "table",
    },
    "black_cells": {
        "primary_agent": "availability_agent",
        "allowed_tables": ["nps_enhancement_black_cells"],
        "anti_hallucination": [
            "Do NOT include NPS or alarm data",
            "Query ONLY the black_cells table",
            "Do NOT conflate black cells with general availability KPIs",
        ],
        "output_format": "table",
    },
    "complaint": {
        "primary_agent": "customer_experience_agent",
        "allowed_tables": ["nps_enhancement_complaint_analysis"],
        "anti_hallucination": [
            "Do NOT include churn data",
            "Do NOT query NPS score table",
            "Report ONLY complaint records from the complaint_analysis table",
        ],
        "output_format": "table",
    },
    "churn": {
        "primary_agent": "customer_experience_agent",
        "allowed_tables": ["nps_enhancement_weekly_churn", "nps_enhancement_churn_cxi_demarcation", "nps_enhancement_nps_cxi_demarcation", "nps_enhancement_complain_cxi_demarcation"],
        "anti_hallucination": [
            "Do NOT include complaint text data",
            "Do NOT query NPS score table",
            "Report ONLY churn counts from the weekly_churn table",
        ],
        "output_format": "table",
    },
    "topology": {
        "primary_agent": "topology_agent",
        "allowed_tables": [
            "nps_enhancement_topology",
            "nps_enhancements_auto_tt_dual_cut_path_cache",
            "nps_enhancements_auto_tt_dual_cut_path_cache_true",
            "nps_enhancements_auto_tt_dual_cut_risk_cache",
            "nps_enhancements_auto_tt_dual_cut_risk_cache_true",
            "nps_enhancements_auto_tt_dual_cut_spof_cache",
            "nps_enhancements_auto_tt_dual_cut_spof_cache_true",
        ],
        "anti_hallucination": [
            "Do NOT include alarm or KPI data",
            "Do NOT query availability tables",
            "Report topology paths, SPOF status, and dual-cut risk data",
            "Use path_cache tables for transport paths (not the legacy topology table)",
        ],
        "output_format": "table",
    },
    "anomaly": {
        "primary_agent": "availability_agent",
        "allowed_tables": [
            "nps_enhancement_ran_daily_anomalies",
            "nps_enhancement_ran_daily_trend",
        ],
        "anti_hallucination": [
            "Do NOT include NPS or alarm data",
            "Focus ONLY on KPI anomalies from anomaly detection",
            "Do NOT broaden to other sites unless explicitly asked",
        ],
        "output_format": "table",
    },

    # ─── Investigation Intents (Medium) ─────────────────────────────────────
    "alarm_correlation": {
        "primary_agent": "alarm_agent",
        "expansion_agents": ["availability_agent"],
        "allowed_tables": [
            "nps_enhancement_alarms",
            "nps_enhancement_ran_daily_trend",
        ],
        "anti_hallucination": [
            "Do NOT include NPS score or customer data",
            "Do NOT query ticket or churn tables",
            "Correlate ONLY alarm and availability data",
            "Do NOT fabricate alarm categories not present in the data",
        ],
        "output_format": "table_with_summary",
    },
    "availability_investigation": {
        "primary_agent": "availability_agent",
        "expansion_agents": ["alarm_agent"],
        "allowed_tables": [
            "nps_enhancement_ran_daily_trend",
            "nps_enhancement_ran_daily_anomalies",
            "nps_enhancement_black_cells",
        ],
        "anti_hallucination": [
            "Do NOT include NPS customer scores",
            "Do NOT query ticket or complaint tables",
            "Focus ONLY on RAN KPI metrics and anomalies",
            "Do NOT broaden scope beyond specified site/region",
        ],
        "output_format": "table_with_summary",
    },
    "ticket_analysis": {
        "primary_agent": "ticket_agent",
        "expansion_agents": ["alarm_agent"],
        "allowed_tables": [
            "nps_enhancement_open_tickets",
            "nps_enhancement_closed_tickets",
            "nps_enhancement_alarms",
        ],
        "anti_hallucination": [
            "Do NOT include NPS or KPI metric data",
            "Do NOT query availability trend tables",
            "Focus on ticket patterns, counts, and descriptions",
            "Do NOT fabricate ticket descriptions not in the data",
        ],
        "output_format": "table_with_summary",
    },
    "customer_impact": {
        "primary_agent": "customer_experience_agent",
        "expansion_agents": ["availability_agent"],
        "allowed_tables": [
            "nps_enhancement_nps",
            "nps_enhancement_weekly_churn",
            "nps_enhancement_complaint_analysis",
            "nps_enhancement_forecast_nps",
        ],
        "anti_hallucination": [
            "Do NOT include raw alarm or RAN KPI data",
            "Do NOT query battery or topology tables",
            "Focus ONLY on customer-facing metrics: NPS, churn, complaints, NPS forecast",
            "Do NOT infer causation without evidence from the allowed tables",
        ],
        "output_format": "table_with_summary",
    },
    "infrastructure": {
        "primary_agent": "power_agent",
        "expansion_agents": ["topology_agent", "alarm_agent"],
        "allowed_tables": [
            "nps_enhancement_battery",
            "nps_enhancement_topology",
            "nps_enhancement_alarms",
            "nps_enhancement_weekly_chronic_down",
            "nps_enhancements_auto_tt_dual_cut_path_cache",
            "nps_enhancements_auto_tt_dual_cut_spof_cache",
            "nps_enhancements_auto_tt_dual_cut_risk_cache",
        ],
        "anti_hallucination": [
            "Do NOT include NPS or customer data",
            "Do NOT query KPI trend tables directly",
            "Focus on infrastructure: power, topology, SPOF, dual-cut risk, chronic down",
            "Do NOT fabricate topology paths not in the data",
        ],
        "output_format": "table_with_summary",
    },
    "root_cause": {
        "primary_agent": "root_cause_agent",
        "expansion_agents": ["availability_agent", "alarm_agent", "ticket_agent", "power_agent"],
        "allowed_tables": [
            "nps_enhancement_ran_daily_trend",
            "nps_enhancement_alarms",
            "nps_enhancement_open_tickets",
            "nps_enhancement_nps",
            "nps_enhancement_battery",
            "nps_enhancement_topology",
            "nps_enhancement_forecast_nps",
            "nps_enhancements_auto_tt_dual_cut_path_cache",
            "nps_enhancements_auto_tt_dual_cut_spof_cache",
            "nps_enhancements_auto_tt_dual_cut_risk_cache",
        ],
        "anti_hallucination": [
            "Do NOT fabricate root cause without evidence from multiple domains",
            "Do NOT present correlation as causation",
            "Each root cause hypothesis MUST cite supporting evidence tables",
            "Confidence score must reflect evidence completeness",
            "Include SPOF status and dual-cut risk in transport-related root causes",
            "NEVER attribute root cause to prior-day alarms that were FULLY CLEARED before degradation date",
            "RF Unit Power Supply alarms are POWER failures, NOT RF interference",
            "Cancelled/NSA tickets must be IGNORED — do not cite as evidence",
            "If alarm was self-healed (cleared within 60min with recovery), it is NOT the root cause of later degradation",
        ],
        "output_format": "structured_report",
    },

    # ─── Fallback ───────────────────────────────────────────────────────────
    "general": {
        "primary_agent": "nl2sql_agent",
        "allowed_tables": ALL_TABLES,  # No restriction for general queries
        "anti_hallucination": [
            "Answer ONLY from data in the database",
            "Do NOT fabricate information not present in query results",
            "If unsure, say so rather than guessing",
        ],
        "output_format": "table",
    },
}


# =============================================================================
# PUBLIC API
# =============================================================================

def get_context_for_intent(intent_type: str) -> dict:
    """
    Get the full context constraint set for a given intent.

    Returns:
        {
            "primary_agent": str,
            "expansion_agents": list[str],
            "allowed_tables": list[str],
            "forbidden_tables": list[str],
            "anti_hallucination": list[str],
            "output_format": str,
        }
    """
    ctx = INTENT_REGISTRY.get(intent_type, INTENT_REGISTRY["general"])

    allowed = ctx["allowed_tables"]
    forbidden = _forbidden_from_allowed(allowed)

    return {
        "primary_agent": ctx["primary_agent"],
        "expansion_agents": ctx.get("expansion_agents", []),
        "allowed_tables": allowed,
        "forbidden_tables": forbidden,
        "anti_hallucination": ctx["anti_hallucination"],
        "output_format": ctx.get("output_format", "table"),
    }


def get_table_visibility_prompt(intent_type: str) -> str:
    """
    Generate the table visibility instruction to inject into NL2SQL prompt.

    Returns a formatted string that restricts which tables the LLM can reference.
    """
    ctx = get_context_for_intent(intent_type)

    lines = [
        "",
        "=" * 60,
        "TABLE ACCESS CONTROL (enforced — violations will be rejected)",
        "=" * 60,
        "",
        "ALLOWED TABLES (you may ONLY query these):",
    ]
    for table in ctx["allowed_tables"]:
        lines.append(f"  - {table}")

    lines.append("")
    lines.append("FORBIDDEN TABLES (do NOT reference — SQL will be rejected):")
    for table in ctx["forbidden_tables"]:
        lines.append(f"  - {table}")

    lines.append("")
    lines.append("CONSTRAINTS:")
    for rule in ctx["anti_hallucination"]:
        lines.append(f"  - {rule}")

    lines.append("=" * 60)

    return "\n".join(lines)


def get_anti_hallucination_prompt(intent_type: str) -> str:
    """
    Generate the anti-hallucination constraint block to append to agent prompts.
    """
    ctx = get_context_for_intent(intent_type)

    lines = [
        "",
        "ANTI-HALLUCINATION CONSTRAINTS (strictly enforced):",
    ]
    for rule in ctx["anti_hallucination"]:
        lines.append(f"  - {rule}")

    lines.append("")
    lines.append(f"ALLOWED DATA SOURCES: {', '.join(ctx['allowed_tables'])}")
    lines.append(f"OUTPUT FORMAT: {ctx['output_format']}")

    return "\n".join(lines)


def validate_intent_tables(intent_type: str, sql: str) -> dict:
    """
    Convenience function: validates SQL against the intent's table constraints.

    Returns the same format as sql_tools.validate_sql().
    """
    ctx = get_context_for_intent(intent_type)

    from tools.sql_tools import validate_sql
    return validate_sql(
        sql,
        forbidden_tables=ctx["forbidden_tables"],
        allowed_tables=ctx["allowed_tables"],
    )
