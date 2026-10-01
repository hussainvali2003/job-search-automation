from collector.core.models import Source
from collector.sources.base import JobSource, MockSource
from collector.sources.ats.greenhouse import GreenhouseSource
from collector.sources.ats.lever import LeverSource
from collector.sources.ats.ashby import AshbySource
from collector.sources.ats.workable import WorkableSource
from collector.sources.ats.smartrecruiters import SmartRecruitersSource
from collector.sources.ats.recruitee import RecruiteeSource
from collector.sources.ats.bamboohr import BambooHRSource

def create_adapter(source: Source) -> JobSource:
    platform = (source.ats_platform or "").lower()
    if platform == "greenhouse":
        return GreenhouseSource(source)
    elif platform == "lever":
        return LeverSource(source)
    elif platform == "ashby":
        return AshbySource(source)
    elif platform == "workable":
        return WorkableSource(source)
    elif platform == "smartrecruiters":
        return SmartRecruitersSource(source)
    elif platform == "recruitee":
        return RecruiteeSource(source)
    elif platform == "bamboohr":
        return BambooHRSource(source)
    else:
        return MockSource(source)
