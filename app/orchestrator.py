"""Runs all four modules against a parsed campaign and assembles the report."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.claimcheck import run_claimcheck
from app.modules.comparative import run_comparative_check
from app.modules.consumer_protection import run_consumer_protection_check
from app.modules.contract_cross_check import run_contract_cross_check
from app.modules.disclosure import run_disclosure_check
from app.modules.music import run_music_check
from app.pipeline import Issue
from app.scoring import CampaignReport, score_campaign


@dataclass
class CampaignInput:
    brand: str
    product: str
    objective: str
    target_audience: str
    claims_to_communicate: str
    contract_text: str
    content_text: str
    audio_bytes: bytes | None = None
    audio_filename: str = ""


@dataclass
class RunResult:
    report: CampaignReport
    details: dict  # module -> detail dict from that module


def run_all_modules(campaign: CampaignInput) -> RunResult:
    all_issues: list[Issue] = []
    details: dict = {}

    disclosure_issues, disclosure_detail = run_disclosure_check(campaign.content_text)
    all_issues += disclosure_issues
    details["disclosure"] = disclosure_detail

    claims_issues, claims_detail = run_claimcheck(
        campaign.content_text, campaign.claims_to_communicate
    )
    all_issues += claims_issues
    details["claims"] = claims_detail

    brief_text_for_comparative = (
        f"Objective: {campaign.objective}\nClaims to communicate: {campaign.claims_to_communicate}"
    )
    comparative_issues, comparative_detail = run_comparative_check(
        campaign.content_text, brief_text_for_comparative
    )
    all_issues += comparative_issues
    details["comparative"] = comparative_detail

    contract_issues, contract_detail = run_contract_cross_check(
        campaign.contract_text, campaign.content_text
    )
    all_issues += contract_issues
    details["contract"] = contract_detail

    music_issues, music_detail = run_music_check(campaign.audio_bytes, campaign.audio_filename)
    all_issues += music_issues
    details["music"] = music_detail

    cp_issues, cp_detail = run_consumer_protection_check(
        campaign.content_text, brief_text_for_comparative
    )
    all_issues += cp_issues
    details["consumer_protection"] = cp_detail

    report = score_campaign(all_issues)
    return RunResult(report=report, details=details)
