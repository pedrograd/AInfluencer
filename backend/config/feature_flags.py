from dataclasses import dataclass

from config.settings import settings


@dataclass(frozen=True)
class FeatureFlags:
    enable_advanced: bool
    enable_upscale: bool
    enable_face_restore: bool
    enable_batch: bool
    enable_high_res: bool
    demo_mode: bool
    demo_max_width: int
    demo_max_height: int
    demo_max_batch: int


def get_feature_flags() -> FeatureFlags:
    """Return current feature flags derived from settings."""
    return FeatureFlags(
        enable_advanced=settings.enable_advanced and not settings.demo_mode,
        enable_upscale=settings.enable_upscale and not settings.demo_mode,
        enable_face_restore=settings.enable_face_restore and not settings.demo_mode,
        enable_batch=settings.enable_batch and not settings.demo_mode,
        enable_high_res=settings.enable_high_res and not settings.demo_mode,
        demo_mode=settings.demo_mode,
        demo_max_width=settings.demo_max_width,
        demo_max_height=settings.demo_max_height,
        demo_max_batch=settings.demo_max_batch,
    )

