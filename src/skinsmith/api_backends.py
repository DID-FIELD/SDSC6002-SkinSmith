from __future__ import annotations

import base64
import io
import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image

from .design_routes import AssetCreativeProfile
from .mapped_readability import DesignElement, ElementReadability


class ApiBackendError(RuntimeError):
    """A provider request or response could not be used by SkinSmith."""


JsonTransport = Callable[
    [str, str, Mapping[str, str], Mapping[str, Any], float], Mapping[str, Any]
]


def _default_json_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, Any],
    timeout: float,
) -> Mapping[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=dict(headers),
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed provider URLs
            body = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ApiBackendError(f"provider returned HTTP {error.code}: {detail[:1000]}") from error
    except URLError as error:
        raise ApiBackendError(f"provider request failed: {error.reason}") from error
    try:
        value = json.loads(body)
    except json.JSONDecodeError as error:
        raise ApiBackendError("provider returned a non-JSON response") from error
    if not isinstance(value, dict):
        raise ApiBackendError("provider response must be a JSON object")
    return value


def _theme_schema(component_names: Sequence[str], style_ids: Sequence[str]) -> dict[str, Any]:
    string_array = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    element = {
        "type": "object",
        "properties": {
            "element_id": {"type": "string"},
            "display_name": {"type": "string"},
            "semantic_role": {
                "type": "string",
                "enum": ["hero", "secondary", "connector", "background"],
            },
            "generation_description": {"type": "string"},
        },
        "required": [
            "element_id",
            "display_name",
            "semantic_role",
            "generation_description",
        ],
        "additionalProperties": False,
    }
    story = {
        "type": "object",
        "properties": {
            "component": {"type": "string", "enum": list(component_names)},
            "narrative_role": {"type": "string"},
            "element_ids": string_array,
            "prominence": {"type": "number", "minimum": 0, "maximum": 1},
            "detail_density": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": [
            "component",
            "narrative_role",
            "element_ids",
            "prominence",
            "detail_density",
        ],
        "additionalProperties": False,
    }
    properties: dict[str, Any] = {
        "theme_id": {"type": "string"},
        "display_name": {"type": "string"},
        "generation_label": {"type": "string"},
        "match_terms": string_array,
        "concept": {"type": "string"},
        "narrative": {"type": "string"},
        "default_style_id": {"type": "string", "enum": list(style_ids)},
        "palette": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 8,
        },
        "elements": {"type": "array", "items": element, "minItems": 8, "maxItems": 14},
        "pattern_notes": string_array,
        "component_story": {
            "type": "array",
            "items": story,
            "minItems": len(component_names),
            "maxItems": len(component_names),
        },
        "evaluation_criteria": string_array,
        "reference_policy": {"type": "string"},
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _style_schema(component_names: Sequence[str]) -> dict[str, Any]:
    string_array = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    route_policy = {
        "type": "object",
        "properties": {
            "objective": {"type": "string"},
            "composition_rules": string_array,
            "constraints": string_array,
        },
        "required": ["objective", "composition_rules", "constraints"],
        "additionalProperties": False,
    }
    direction = {
        "type": "object",
        "properties": {
            "direction_id": {"type": "string"},
            "title": {"type": "string"},
            "concept": {"type": "string"},
            "motifs": string_array,
            "route_a_emphasis": {"type": "string"},
            "route_b_emphasis": {"type": "string"},
        },
        "required": [
            "direction_id",
            "title",
            "concept",
            "motifs",
            "route_a_emphasis",
            "route_b_emphasis",
        ],
        "additionalProperties": False,
    }
    component_roles = {
        "type": "object",
        "properties": {component: {"type": "string"} for component in component_names},
        "required": list(component_names),
        "additionalProperties": False,
    }
    properties: dict[str, Any] = {
        "style_id": {"type": "string"},
        "display_name": {"type": "string"},
        "generation_label": {"type": "string"},
        "match_terms": string_array,
        "summary": {"type": "string"},
        "visual_vocabulary": string_array,
        "motifs": string_array,
        "palette": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 8,
        },
        "material_cues": string_array,
        "composition_principles": string_array,
        "avoid": string_array,
        "route_a": route_policy,
        "route_b": route_policy,
        "component_roles": component_roles,
        "candidate_directions": {
            "type": "array",
            "items": direction,
            "minItems": 4,
            "maxItems": 4,
        },
        "evaluation_criteria": string_array,
        "reference_policy": {"type": "string"},
        "procedural_fallback_motif": {
            "type": "string",
            "enum": ["waves", "diagonal", "circuits"],
        },
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _theme_prompt(
    brief: str,
    asset: AssetCreativeProfile,
    style_ids: Sequence[str],
) -> str:
    return (
        "You are SkinSmith's art director. Compile the user's arbitrary theme into an original, "
        "executable weapon-skin art plan. Do not merely repeat the theme word or propose generic lines. "
        "Define 8-14 concrete hero, related-symbol, environment, architecture/nature, connector, "
        "atmosphere, background, and micro-detail elements. Infer the broader visual world implied "
        "by the brief: for example a Chinese dragon may imply clouds, waves, treasure, flaming pearls, "
        "mountains, lightning, mist, jade, and architectural ornament; a landscape may imply mountains, "
        "water, pavilions, bridges, bamboo, travellers, boats, sun or moon, birds, and mist. Select a "
        "coherent subset rather than merely repeating the theme word. Route A must support a dense, "
        "crop-tolerant all-over template. Route B must tell one coherent whole-weapon story whose final square "
        "is a fragmented UV atlas, not a standalone poster. Respect the weapon silhouette and assign every "
        "listed component. The default Route B uses one crop-robust master artwork, so do not emit optional "
        "composition_groups in this structured response; explicit per-group composition remains a separate "
        "research branch for hand-authored cached themes. "
        "The receiver is the default focal surface and barrel/muzzle is quiet by default, but set "
        "allow_muzzle_focus=true when the concept intentionally places a focal subject there. Use only original "
        "or rights-safe visual references; never imitate a living artist or copy a named skin. Return only the "
        "requested JSON.\n\n"
        f"USER BRIEF:\n{brief}\n\n"
        f"TARGET WEAPON PROFILE:\n{json.dumps(asset.compiler_context(), ensure_ascii=False)}\n\n"
        f"AVAILABLE STYLE IDS:\n{json.dumps(list(style_ids), ensure_ascii=False)}"
    )


def _style_prompt(
    brief: str,
    theme_context: Mapping[str, Any],
    asset_context: Mapping[str, Any],
) -> str:
    return (
        "You are SkinSmith's visual-style director. Create an original executable StylePack for the "
        "provided theme and weapon. Decide the appropriate medium and visual system from the theme itself: "
        "material themes such as marble require geological grain, polished stone, fracture scale and metallic "
        "inlay cues; illustration themes require an appropriate graphic language; technical themes require "
        "designed structure rather than generic random lines. Do not force the result into a cached style. "
        "Route A must be a dense crop-tolerant seamless template. Default Route B will generate multiple "
        "landscape master artworks and automatically map them through the weapon OBJ/UV. Its source art must "
        "contain many medium and small thematic clusters, rich related elements, little dead space, and no "
        "single full-width subject. Provide four genuinely different candidate directions within one coherent "
        "style, varying composition rhythm, material treatment, atmosphere, and motif hierarchy. Avoid baked "
        "lighting, fake 3D weapon mockups, "
        "text, logos, copyrighted characters, named skins, and imitation of living artists. Return only the "
        "requested JSON.\n\n"
        f"USER BRIEF:\n{brief}\n\n"
        f"VALIDATED THEME:\n{json.dumps(theme_context, ensure_ascii=False)}\n\n"
        f"TARGET WEAPON PROFILE:\n{json.dumps(asset_context, ensure_ascii=False)}"
    )


def _parse_json_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ApiBackendError("provider structured output was not valid JSON") from error
    if not isinstance(value, dict):
        raise ApiBackendError("provider structured output must be a JSON object")
    return value


def _find_text_blocks(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        output_text = value.get("output_text")
        if isinstance(output_text, str):
            found.append(output_text)
        if value.get("type") in {"output_text", "text"} and isinstance(value.get("text"), str):
            found.append(value["text"])
        for child in value.values():
            found.extend(_find_text_blocks(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_find_text_blocks(child))
    return found


def _normalize_theme(value: Mapping[str, Any], asset: AssetCreativeProfile) -> dict[str, Any]:
    data = dict(value)
    stories = data.get("component_story")
    if not isinstance(stories, list):
        raise ApiBackendError("provider theme component_story must be an array")
    mapped: dict[str, Any] = {}
    for story in stories:
        if not isinstance(story, dict) or not isinstance(story.get("component"), str):
            raise ApiBackendError("provider theme contains an invalid component story")
        component = story["component"]
        if component in mapped:
            raise ApiBackendError(f"provider theme repeats component: {component}")
        mapped[component] = {key: value for key, value in story.items() if key != "component"}
    expected = set(asset.component_anchors)
    if set(mapped) != expected:
        raise ApiBackendError(
            f"provider theme components do not match target weapon: expected {sorted(expected)}"
        )
    data["component_story"] = mapped
    return data


@dataclass(frozen=True)
class ApiCallTrace:
    provider: str
    model: str
    endpoint: str
    api_key_env: str
    request: Mapping[str, Any]
    response: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "api_key_env": self.api_key_env,
            "api_key_recorded": False,
            "request": self.request,
            "response": self.response,
        }


class StructuredThemeApiBackend:
    provider = "base"
    endpoint = ""

    def __init__(
        self,
        model: str,
        *,
        api_key_env: str,
        style_ids: Sequence[str],
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        if not style_ids:
            raise ValueError("style_ids must not be empty")
        self.model = model.strip()
        self.api_key_env = api_key_env
        self.style_ids = tuple(style_ids)
        self.transport = transport or _default_json_transport
        self.timeout = timeout
        self.last_trace: ApiCallTrace | None = None

    @property
    def backend_id(self) -> str:
        return f"{self.provider}:{self.model}"

    def _headers(self, api_key: str) -> dict[str, str]:
        raise NotImplementedError

    def _payload(self, prompt: str, schema: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def __call__(self, brief: str, asset: AssetCreativeProfile) -> Mapping[str, Any]:
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise ApiBackendError(
                f"{self.api_key_env} is not configured; set it locally and never commit the key"
            )
        schema = _theme_schema(tuple(asset.component_anchors), self.style_ids)
        prompt = _theme_prompt(brief, asset, self.style_ids)
        payload = self._payload(prompt, schema)
        response = self.transport(
            "POST", self.endpoint, self._headers(api_key), payload, self.timeout
        )
        self.last_trace = ApiCallTrace(
            provider=self.provider,
            model=self.model,
            endpoint=self.endpoint,
            api_key_env=self.api_key_env,
            request=payload,
            response=response,
        )
        texts = _find_text_blocks(response)
        if not texts:
            raise ApiBackendError("provider response did not contain structured output text")
        return _normalize_theme(_parse_json_text(texts[-1]), asset)


class OpenAIThemeBackend(StructuredThemeApiBackend):
    provider = "openai"
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        model: str = "gpt-5.4-mini",
        *,
        api_key_env: str = "OPENAI_API_KEY",
        style_ids: Sequence[str],
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(
            model,
            api_key_env=api_key_env,
            style_ids=style_ids,
            transport=transport,
            timeout=timeout,
        )

    def _headers(self, api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _payload(self, prompt: str, schema: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": "Produce a validated SkinSmith art-direction object.",
                },
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "skinsmith_theme_pack",
                    "strict": True,
                    "schema": schema,
                }
            },
        }


class GeminiThemeBackend(StructuredThemeApiBackend):
    provider = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(
        self,
        model: str = "gemini-3.1-flash-lite",
        *,
        api_key_env: str = "GEMINI_API_KEY",
        style_ids: Sequence[str],
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(
            model,
            api_key_env=api_key_env,
            style_ids=style_ids,
            transport=transport,
            timeout=timeout,
        )

    def _headers(self, api_key: str) -> dict[str, str]:
        return {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        }

    def _payload(self, prompt: str, schema: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": [{"type": "text", "text": prompt}],
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        }


class StructuredStyleApiBackend:
    provider = "base"
    endpoint = ""

    def __init__(
        self,
        model: str,
        *,
        api_key_env: str,
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        self.model = model.strip()
        self.api_key_env = api_key_env
        self.transport = transport or _default_json_transport
        self.timeout = timeout
        self.last_trace: ApiCallTrace | None = None

    @property
    def backend_id(self) -> str:
        return f"{self.provider}:{self.model}:style"

    def _headers(self, api_key: str) -> dict[str, str]:
        raise NotImplementedError

    def _payload(self, prompt: str, schema: Mapping[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def __call__(
        self,
        brief: str,
        theme_context: Mapping[str, Any],
        asset_context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise ApiBackendError(
                f"{self.api_key_env} is not configured; set it locally and never commit the key"
            )
        components = asset_context.get("components")
        if not isinstance(components, list) or not components:
            raise ApiBackendError("asset context does not contain components")
        component_names = tuple(
            str(item["component"])
            for item in components
            if isinstance(item, dict) and isinstance(item.get("component"), str)
        )
        if len(component_names) != len(components):
            raise ApiBackendError("asset context contains an invalid component")
        schema = _style_schema(component_names)
        prompt = _style_prompt(brief, theme_context, asset_context)
        payload = self._payload(prompt, schema)
        response = self.transport(
            "POST", self.endpoint, self._headers(api_key), payload, self.timeout
        )
        self.last_trace = ApiCallTrace(
            provider=self.provider,
            model=self.model,
            endpoint=self.endpoint,
            api_key_env=self.api_key_env,
            request=payload,
            response=response,
        )
        texts = _find_text_blocks(response)
        if not texts:
            raise ApiBackendError("provider response did not contain structured style output")
        return _parse_json_text(texts[-1])


class OpenAIStyleBackend(StructuredStyleApiBackend):
    provider = "openai"
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        model: str = "gpt-5.4-mini",
        *,
        api_key_env: str = "OPENAI_API_KEY",
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(
            model,
            api_key_env=api_key_env,
            transport=transport,
            timeout=timeout,
        )

    def _headers(self, api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _payload(self, prompt: str, schema: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": "Produce a validated SkinSmith visual-style object.",
                },
                {"role": "user", "content": prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "skinsmith_style_pack",
                    "strict": True,
                    "schema": schema,
                }
            },
        }


class GeminiStyleBackend(StructuredStyleApiBackend):
    provider = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(
        self,
        model: str = "gemini-3.1-flash-lite",
        *,
        api_key_env: str = "GEMINI_API_KEY",
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(
            model,
            api_key_env=api_key_env,
            transport=transport,
            timeout=timeout,
        )

    def _headers(self, api_key: str) -> dict[str, str]:
        return {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        }

    def _payload(self, prompt: str, schema: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": [{"type": "text", "text": prompt}],
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        }


class GeminiSemanticSourceReviewer:
    """Strict multimodal semantic gate for one generated Route-B source."""

    provider = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(
        self,
        model: str = "gemini-3.1-flash-lite",
        *,
        api_key_env: str = "GEMINI_API_KEY",
        transport: JsonTransport | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.transport = transport or _default_json_transport
        self.timeout = timeout
        self.last_trace: ApiCallTrace | None = None

    @property
    def backend_id(self) -> str:
        return f"{self.provider}:{self.model}:source-review"

    def __call__(
        self,
        role: str,
        prompt: str,
        image: Image.Image,
    ) -> tuple[bool, str]:
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise ApiBackendError(
                f"{self.api_key_env} is not configured; set it locally and never commit the key"
            )
        schema = {
            "type": "object",
            "properties": {
                "passed": {"type": "boolean"},
                "summary": {"type": "string"},
                "depicted_subjects": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "violations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "passed",
                "summary",
                "depicted_subjects",
                "violations",
            ],
            "additionalProperties": False,
        }
        if role == "master_artwork":
            review_prompt = (
                "Act as a composition and forbidden-content gate for one generated landscape "
                "2D master artwork "
                "that will later be automatically cut into a game-asset UV atlas. Do not judge "
                "whether a named anatomical part lands on a weapon component. Do verify that the "
                "image is richly populated with multiple distinct medium/small thematic, symbolic, "
                "environmental, atmospheric, and micro-detail clusters; that no single subject "
                "dominates or spans the complete width; and that large dead or near-black regions "
                "are absent. Reject any visible or implied "
                "firearm, weapon silhouette, weapon part, mockup, product render, UV layout, "
                "text, logo, watermark, border, framed panel, material sample board, or "
                "presentation board. Judge the supplied image against the source contract below. "
                "If uncertain about a forbidden object, reject and state one concise correction."
                "\n\nSOURCE CONTRACT:\n"
                f"{prompt}"
            )
        else:
            review_prompt = (
                "Act as a strict semantic acceptance gate for one generated 2D game-skin "
                f"source asset. Expected semantic role: {role}. Review the supplied image "
                "against the complete source contract below. Pass only when the requested "
                "subject and requested partial anatomy/form are clearly present and no "
                "forbidden content is visible. Reject wrong motifs; complete animals when "
                "only a body, head, or short segment was requested; weapons or weapon parts; "
                "mockups; UV layouts; text; logos; rectangular material slabs, plates, frames, "
                "or presentation boards. Judge content compliance, not general prettiness. "
                "If uncertain, reject and state one concise correction.\n\n"
                f"SOURCE CONTRACT:\n{prompt}"
            )
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        inputs = [
            {"type": "text", "text": review_prompt},
            {
                "type": "image",
                "mime_type": "image/png",
                "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
            },
        ]
        payload = {
            "model": self.model,
            "input": inputs,
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        }
        response = self.transport(
            "POST",
            self.endpoint,
            {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
                "Api-Revision": "2026-05-20",
            },
            payload,
            self.timeout,
        )
        trace_payload = {
            **payload,
            "input": [
                (
                    {
                        **item,
                        "data": "<inline image data omitted; source hash is recorded by the caller>",
                    }
                    if item.get("type") == "image"
                    else dict(item)
                )
                for item in inputs
            ],
        }
        self.last_trace = ApiCallTrace(
            provider=self.provider,
            model=self.model,
            endpoint=self.endpoint,
            api_key_env=self.api_key_env,
            request=trace_payload,
            response=response,
        )
        texts = _find_text_blocks(response)
        if not texts:
            raise ApiBackendError("Gemini semantic review response did not contain text")
        try:
            result = json.loads(texts[-1])
        except json.JSONDecodeError as error:
            raise ApiBackendError(
                "Gemini semantic review response was not valid JSON"
            ) from error
        if not isinstance(result, dict) or not isinstance(result.get("passed"), bool):
            raise ApiBackendError("Gemini semantic review response has an invalid shape")
        summary = str(result.get("summary", "")).strip()
        violations = [
            str(item).strip()
            for item in result.get("violations", ())
            if str(item).strip()
        ]
        status = summary or ("semantic source accepted" if result["passed"] else "semantic mismatch")
        if violations:
            status = f"{status}; violations: {'; '.join(violations)}"
        return bool(result["passed"]), status


class GeminiMappedReadabilityReviewer:
    """Compare planned design elements with source and mapped weapon views."""

    provider = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(
        self,
        model: str = "gemini-3.1-flash-lite",
        *,
        api_key_env: str = "GEMINI_API_KEY",
        transport: JsonTransport | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.transport = transport or _default_json_transport
        self.timeout = timeout
        self.last_trace: ApiCallTrace | None = None

    @property
    def backend_id(self) -> str:
        return f"{self.provider}:{self.model}:mapped-readability"

    def __call__(
        self,
        elements: Sequence[DesignElement],
        source: Image.Image,
        views: Mapping[str, Image.Image],
    ) -> tuple[ElementReadability, ...]:
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise ApiBackendError(
                f"{self.api_key_env} is not configured; set it locally and never commit the key"
            )
        if not elements:
            raise ValueError("mapped readability requires design elements")
        if set(views) != {"left", "right", "top"}:
            raise ValueError("mapped readability requires left, right, and top views")
        ids = [item.element_id for item in elements]
        if len(ids) != len(set(ids)):
            raise ValueError("design element ids must be unique")
        element_schema = {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "enum": ids},
                "source_score": {"type": "number", "minimum": 0, "maximum": 1},
                "left_score": {"type": "number", "minimum": 0, "maximum": 1},
                "right_score": {"type": "number", "minimum": 0, "maximum": 1},
                "top_score": {"type": "number", "minimum": 0, "maximum": 1},
                "best_view": {
                    "type": "string",
                    "enum": ["left", "right", "top", "none"],
                },
                "source_evidence": {"type": "string"},
                "mapped_evidence": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": [
                "element_id",
                "source_score",
                "left_score",
                "right_score",
                "top_score",
                "best_view",
                "source_evidence",
                "mapped_evidence",
                "confidence",
            ],
            "additionalProperties": False,
        }
        schema = {
            "type": "object",
            "properties": {
                "elements": {
                    "type": "array",
                    "items": element_schema,
                    "minItems": len(elements),
                    "maxItems": len(elements),
                }
            },
            "required": ["elements"],
            "additionalProperties": False,
        }
        prompt = (
            "Act as an explainable recommendation scorer for a mapped game-skin design. "
            "Image order is exactly: original source artwork, LEFT weapon view, RIGHT weapon "
            "view, TOP weapon view. For every requested design element, score how clearly it "
            "exists in the original source and how clearly a human can recognize it on each "
            "mapped weapon view. A score of 1 means unmistakable and well displayed; 0 means "
            "absent or unreadable. Judge the visible motif itself, not generic colour similarity. "
            "LEFT is the primary presentation view, but report all three independently. Do not "
            "approve or reject the skin and do not choose a winner: these scores are recommendation-"
            "only evidence and human selection remains authoritative. Return exactly one record "
            "per supplied element id.\n\nDESIGN ELEMENTS:\n"
            + json.dumps(
                [
                    {
                        "element_id": item.element_id,
                        "label": item.label,
                        "description": item.description,
                    }
                    for item in elements
                ],
                ensure_ascii=False,
            )
        )
        inputs: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image in (source, views["left"], views["right"], views["top"]):
            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="PNG")
            inputs.append(
                {
                    "type": "image",
                    "mime_type": "image/png",
                    "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                }
            )
        payload = {
            "model": self.model,
            "input": inputs,
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        }
        response = self.transport(
            "POST",
            self.endpoint,
            {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
                "Api-Revision": "2026-05-20",
            },
            payload,
            self.timeout,
        )
        trace_payload = {
            **payload,
            "input": [
                (
                    {
                        **item,
                        "data": "<inline image data omitted; image hashes are recorded by the caller>",
                    }
                    if item.get("type") == "image"
                    else dict(item)
                )
                for item in inputs
            ],
        }
        self.last_trace = ApiCallTrace(
            provider=self.provider,
            model=self.model,
            endpoint=self.endpoint,
            api_key_env=self.api_key_env,
            request=trace_payload,
            response=response,
        )
        texts = _find_text_blocks(response)
        if not texts:
            raise ApiBackendError("mapped readability response did not contain text")
        result = _parse_json_text(texts[-1])
        records = result.get("elements")
        if not isinstance(records, list):
            raise ApiBackendError("mapped readability response has no element array")
        matches = tuple(ElementReadability(**item) for item in records)
        returned_ids = [item.element_id for item in matches]
        if len(returned_ids) != len(set(returned_ids)) or set(returned_ids) != set(ids):
            raise ApiBackendError("mapped readability response does not match element ids")
        return matches


def _find_image_blocks(value: Any) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        data = value.get("data")
        mime_type = value.get("mime_type") or value.get("mimeType")
        if (
            isinstance(data, str)
            and (value.get("type") in {"image", "output_image"} or str(mime_type).startswith("image/"))
        ):
            found.append((data, str(mime_type or "image/png")))
        for child in value.values():
            found.extend(_find_image_blocks(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_find_image_blocks(child))
    return found


class CreativeImageApiBackend:
    provider = "base"
    endpoint = ""

    def __init__(
        self,
        model: str,
        *,
        api_key_env: str,
        transport: JsonTransport | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.transport = transport or _default_json_transport
        self.timeout = timeout
        self.last_trace: ApiCallTrace | None = None

    @property
    def backend_id(self) -> str:
        return f"{self.provider}:{self.model}"

    def _headers(self, api_key: str) -> dict[str, str]:
        raise NotImplementedError

    def _payload(self, prompt: str) -> dict[str, Any]:
        raise NotImplementedError

    def _decode_image(self, response: Mapping[str, Any]) -> Image.Image:
        raise NotImplementedError

    def generate_image(self, prompt: str) -> Image.Image:
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise ApiBackendError(
                f"{self.api_key_env} is not configured; set it locally and never commit the key"
            )
        payload = self._payload(prompt)
        response = self.transport(
            "POST", self.endpoint, self._headers(api_key), payload, self.timeout
        )
        self.last_trace = ApiCallTrace(
            provider=self.provider,
            model=self.model,
            endpoint=self.endpoint,
            api_key_env=self.api_key_env,
            request=payload,
            response=response,
        )
        return self._decode_image(response)


class OpenAIImageBackend(CreativeImageApiBackend):
    provider = "openai"
    endpoint = "https://api.openai.com/v1/images/generations"

    def __init__(
        self,
        model: str = "gpt-image-2",
        *,
        api_key_env: str = "OPENAI_API_KEY",
        quality: str = "medium",
        size: str = "1024x1024",
        transport: JsonTransport | None = None,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(
            model,
            api_key_env=api_key_env,
            transport=transport,
            timeout=timeout,
        )
        self.quality = quality
        self.size = size

    def _headers(self, api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _payload(self, prompt: str) -> dict[str, Any]:
        size = (
            "1024x1024"
            if "tileable game weapon-skin" in prompt
            or "Output only the square" in prompt
            else self.size
        )
        return {
            "model": self.model,
            "prompt": prompt,
            "quality": self.quality,
            "size": size,
        }

    def _decode_image(self, response: Mapping[str, Any]) -> Image.Image:
        values = response.get("data")
        encoded = values[0].get("b64_json") if isinstance(values, list) and values else None
        if not isinstance(encoded, str):
            raise ApiBackendError("OpenAI response did not contain data[0].b64_json")
        return Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")


class GeminiImageBackend(CreativeImageApiBackend):
    provider = "gemini"
    endpoint = "https://generativelanguage.googleapis.com/v1beta/interactions"

    def __init__(
        self,
        model: str = "gemini-3.1-flash-image",
        *,
        api_key_env: str = "GEMINI_API_KEY",
        image_size: str = "1K",
        aspect_ratio: str = "16:9",
        transport: JsonTransport | None = None,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(
            model,
            api_key_env=api_key_env,
            transport=transport,
            timeout=timeout,
        )
        self.image_size = image_size
        self.aspect_ratio = aspect_ratio

    def _headers(self, api_key: str) -> dict[str, str]:
        return {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        }

    def _payload(self, prompt: str) -> dict[str, Any]:
        aspect_ratio = (
            "1:1"
            if "tileable game weapon-skin" in prompt
            or "Output only the square" in prompt
            else self.aspect_ratio
        )
        return {
            "model": self.model,
            "input": [{"type": "text", "text": prompt}],
            "response_format": {
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": aspect_ratio,
                "image_size": self.image_size,
            },
        }

    def generate_image_with_references(
        self,
        prompt: str,
        reference_images: Sequence[Image.Image],
    ) -> Image.Image:
        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise ApiBackendError(
                f"{self.api_key_env} is not configured; set it locally and never commit the key"
            )
        if not reference_images:
            return self.generate_image(prompt)
        inputs: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image in reference_images:
            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="PNG")
            inputs.append(
                {
                    "type": "image",
                    "mime_type": "image/png",
                    "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                }
            )
        aspect_ratio = (
            "1:1"
            if "tileable game weapon-skin" in prompt
            or "Output only the square" in prompt
            else self.aspect_ratio
        )
        payload = {
            "model": self.model,
            "input": inputs,
            "response_format": {
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": aspect_ratio,
                "image_size": self.image_size,
            },
        }
        response = self.transport(
            "POST", self.endpoint, self._headers(api_key), payload, self.timeout
        )
        trace_payload = {
            **payload,
            "input": [
                (
                    {
                        **item,
                        "data": "<inline image data omitted; source hash is recorded by the caller>",
                    }
                    if item.get("type") == "image"
                    else dict(item)
                )
                for item in inputs
            ],
        }
        self.last_trace = ApiCallTrace(
            provider=self.provider,
            model=self.model,
            endpoint=self.endpoint,
            api_key_env=self.api_key_env,
            request=trace_payload,
            response=response,
        )
        return self._decode_image(response)

    def _decode_image(self, response: Mapping[str, Any]) -> Image.Image:
        images = _find_image_blocks(response)
        if not images:
            raise ApiBackendError("Gemini response did not contain an image block")
        return Image.open(io.BytesIO(base64.b64decode(images[-1][0]))).convert("RGB")
