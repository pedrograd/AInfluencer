"""API router aggregation module.

This module aggregates all API routers from individual endpoint modules
and registers them with appropriate prefixes and tags for the main
FastAPI application.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.ab_testing import router as ab_testing_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.characters import router as characters_router
from app.api.comfyui import router as comfyui_router
from app.api.content import router as content_router
from app.api.content_intelligence import router as content_intelligence_router
from app.api.errors import router as errors_router
from app.api.generate import router as generate_router
from app.api.health import router as health_router
from app.api.installer import router as installer_router
from app.api.logs import router as logs_router
from app.api.models import router as models_router
from app.api.presets import router as presets_router
from app.api.services import router as services_router
from app.api.scheduling import router as scheduling_router
from app.api.settings import router as settings_router
from app.api.status import router as status_router
from app.api.audio_video_sync import router as audio_video_sync_router
from app.api.instagram import router as instagram_router
from app.api.twitter import router as twitter_router
from app.api.facebook import router as facebook_router
from app.api.telegram import router as telegram_router
from app.api.onlyfans import router as onlyfans_router
from app.api.video_editing import router as video_editing_router
from app.api.video_storage import router as video_storage_router
from app.api.voice import router as voice_router
from app.api.workflows import router as workflows_router
from app.api.posts import router as posts_router
from app.api.automation import router as automation_router
from app.api.payment import router as payment_router
from app.api.youtube import router as youtube_router
from app.api.tiktok import router as tiktok_router
from app.api.linkedin import router as linkedin_router
from app.api.discord import router as discord_router
from app.api.snapchat import router as snapchat_router
from app.api.twitch import router as twitch_router
from app.api.crisis_management import router as crisis_management_router
from app.api.monitoring import router as monitoring_router
from app.api.resources import router as resources_router
from app.api.platform_optimization import router as platform_optimization_router
from app.api.third_party import router as third_party_router
from app.api.public_api import router as public_api_router
from app.api.photo_editing import router as photo_editing_router

router = APIRouter()
router.include_router(ab_testing_router, prefix="/ab-testing", tags=["ab-testing"])
router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
router.include_router(auth_router, prefix="/auth", tags=["authentication"])
router.include_router(health_router, tags=["system"])
router.include_router(status_router, tags=["system"])
router.include_router(errors_router, tags=["system"])
router.include_router(logs_router, tags=["system"])
router.include_router(services_router, prefix="/services", tags=["services"])
router.include_router(installer_router, prefix="/installer", tags=["installer"])
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(generate_router, prefix="/generate", tags=["generate"])
router.include_router(presets_router, prefix="/generate", tags=["generate"])
router.include_router(content_router, prefix="/content", tags=["content"])
router.include_router(comfyui_router, prefix="/comfyui", tags=["comfyui"])
router.include_router(settings_router, prefix="/settings", tags=["settings"])
router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
router.include_router(characters_router, prefix="/characters", tags=["characters"])
router.include_router(scheduling_router, prefix="/scheduling", tags=["scheduling"])
router.include_router(video_editing_router, prefix="/video", tags=["video"])
router.include_router(audio_video_sync_router, prefix="/video", tags=["video"])
router.include_router(video_storage_router, prefix="/content", tags=["content"])
router.include_router(voice_router, prefix="/voice", tags=["voice"])
router.include_router(content_intelligence_router, prefix="/content-intelligence", tags=["content-intelligence"])
router.include_router(instagram_router, prefix="/instagram", tags=["instagram"])
router.include_router(twitter_router, prefix="/twitter", tags=["twitter"])
router.include_router(facebook_router, prefix="/facebook", tags=["facebook"])
router.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
router.include_router(onlyfans_router, prefix="/onlyfans", tags=["onlyfans"])
router.include_router(posts_router, prefix="/posts", tags=["posts"])
router.include_router(automation_router, prefix="/automation", tags=["automation"])
router.include_router(payment_router, prefix="/payment", tags=["payment"])
router.include_router(youtube_router, prefix="/youtube", tags=["youtube"])
router.include_router(tiktok_router, prefix="/tiktok", tags=["tiktok"])
router.include_router(linkedin_router, prefix="/linkedin", tags=["linkedin"])
router.include_router(discord_router, prefix="/discord", tags=["discord"])
router.include_router(snapchat_router, prefix="/snapchat", tags=["snapchat"])
router.include_router(twitch_router, prefix="/twitch", tags=["twitch"])
router.include_router(crisis_management_router, prefix="/crisis", tags=["crisis-management"])
router.include_router(monitoring_router, tags=["monitoring"])
router.include_router(resources_router, prefix="/resources", tags=["resources"])
router.include_router(platform_optimization_router, prefix="/platform", tags=["platform-optimization"])
router.include_router(third_party_router, prefix="/third-party", tags=["third-party"])
router.include_router(public_api_router, tags=["public-api"])
router.include_router(photo_editing_router, prefix="/photo", tags=["photo-editing"])
