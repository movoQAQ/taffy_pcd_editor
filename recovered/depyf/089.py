def _clear_region_preview(self):
    if self.region_preview_actor is not None:
        self.renderer.RemoveActor(self.region_preview_actor)
        self.region_preview_actor = None
        return None
    return None
