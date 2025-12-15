# WORKFLOWS CATALOG - Curated Workflow Packs

**Purpose:** Stub for future workflow support. Keep minimal until MVP works.

---

## Status
**Not Started** - This is a placeholder for Phase 3.

---

## Future Structure

Each workflow pack will define:
- **Required nodes list** (ComfyUI nodes)
- **Required models list** (checkpoints, LoRAs, VAEs)
- **Required extensions list** (ComfyUI custom nodes)
- **Validation checks** (verify all dependencies before run)

---

## Example Workflow Pack (Future)

```json
{
  "id": "portrait-basic",
  "name": "Basic Portrait",
  "description": "Simple portrait generation workflow",
  "required_nodes": ["CheckpointLoaderSimple", "KSampler", "VAEDecode"],
  "required_models": {
    "checkpoints": ["sd_xl_base_1.0.safetensors"],
    "loras": [],
    "vaes": []
  },
  "required_extensions": [],
  "workflow_file": "workflows/portrait-basic.json"
}
```

---

## Notes
- Do NOT include anything framed as "undetectable", "bypass", or "evade"
- Focus on quality, consistency, consent, provenance, UX
- Require consent for any real-person likeness use

