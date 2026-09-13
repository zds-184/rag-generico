"""Descarga y conversión del corpus MITRE ATT&CK (STIX 2.1) a documentos de texto.

Fuente oficial (siempre la última versión publicada):
  https://github.com/mitre-attack/attack-stix-data  ->  <dominio>/<dominio>.json

Cada objeto STIX relevante (técnica, grupo, software, mitigación, táctica, campaña,
fuente/componente de datos) se convierte en un documento Markdown enriquecido con sus
relaciones (procedure examples, mitigaciones, detecciones...). Los documentos se
trocean después con `chunking.split_text`.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import httpx

TYPE_LABELS = {
    "attack-pattern": "technique",
    "intrusion-set": "group",
    "malware": "software",
    "tool": "software",
    "course-of-action": "mitigation",
    "x-mitre-tactic": "tactic",
    "campaign": "campaign",
    "x-mitre-data-source": "data-source",
    "x-mitre-data-component": "data-component",
    # ATT&CK >= v18: las detecciones se modelan como estrategias (DETxxxx) con analíticas (ANxxxx)
    "x-mitre-detection-strategy": "detection-strategy",
}
# Objetos que se resuelven pero NO generan documento propio (su texto se incluye en el padre)
EMBEDDED_TYPES = {"x-mitre-analytic": "analytic"}

_CITATION_RE = re.compile(r"\s*\(Citation:[^)]*\)")


@dataclass
class Document:
    id: str
    title: str
    text: str
    metadata: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- descarga
def download_domain(domain: str, base_url: str, data_dir: str, refresh: bool = False) -> Path:
    path = Path(data_dir) / "corpus" / f"{domain}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not refresh:
        return path
    url = f"{base_url.rstrip('/')}/{domain}/{domain}.json"
    print(f"[corpus] descargando {url}")
    with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with path.open("wb") as fh:
            for chunk in r.iter_bytes():
                fh.write(chunk)
    return path


def load_bundle(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh).get("objects", [])


# --------------------------------------------------------------------------- helpers
def _clean(text: str | None) -> str:
    return _CITATION_RE.sub("", text or "").strip()


def _attack_ref(obj: dict) -> tuple[str | None, str | None]:
    for ref in obj.get("external_references", []):
        src = ref.get("source_name", "")
        if src.startswith("mitre") and "attack" in src and ref.get("external_id"):
            return ref["external_id"], ref.get("url")
    return None, None


def _is_active(obj: dict) -> bool:
    return not obj.get("revoked", False) and not obj.get("x_mitre_deprecated", False)


def _label(obj: dict) -> str:
    aid, _ = _attack_ref(obj)
    return f"{aid} {obj.get('name', '')}".strip() if aid else obj.get("name", "")


def _tactics(obj: dict) -> list[str]:
    return [p["phase_name"] for p in obj.get("kill_chain_phases", []) if p.get("phase_name")]


def _bullets(items: list[str], limit: int | None = None) -> str:
    items = items[:limit] if limit else items
    return "\n".join(f"- {i}" for i in items) if items else "- (none)"


# --------------------------------------------------------------------------- builder
class MitreCorpusBuilder:
    def __init__(self, objects: list[dict], domain: str, max_examples: int = 25):
        self.domain = domain
        self.max_examples = max_examples
        self.version = next(
            (o.get("x_mitre_version") for o in objects if o.get("type") == "x-mitre-collection"), None
        )
        self.by_id: dict[str, dict] = {
            o["id"]: o for o in objects if o.get("type") in TYPE_LABELS and _is_active(o)
        }
        self.analytics: dict[str, dict] = {
            o["id"]: o for o in objects if o.get("type") in EMBEDDED_TYPES and _is_active(o)
        }
        # data component -> estrategias de detección cuyas analíticas lo usan como log source
        self.dc_usage: dict[str, set[str]] = {}
        for strat in self.by_id.values():
            if strat["type"] != "x-mitre-detection-strategy":
                continue
            for an_id in strat.get("x_mitre_analytic_refs", []):
                for ls in self.analytics.get(an_id, {}).get("x_mitre_log_source_references", []):
                    dc = ls.get("x_mitre_data_component_ref")
                    if dc:
                        self.dc_usage.setdefault(dc, set()).add(strat["id"])
        self.rels = [
            r
            for r in objects
            if r.get("type") == "relationship"
            and _is_active(r)
            and r.get("source_ref") in self.by_id
            and r.get("target_ref") in self.by_id
        ]
        # Índices de relaciones por (tipo, extremo)
        self.by_target: dict[tuple[str, str], list[dict]] = {}
        self.by_source: dict[tuple[str, str], list[dict]] = {}
        for r in self.rels:
            self.by_target.setdefault((r["relationship_type"], r["target_ref"]), []).append(r)
            self.by_source.setdefault((r["relationship_type"], r["source_ref"]), []).append(r)

    # ---- accesos a relaciones
    def _sources(self, rel_type: str, target: str, types: tuple[str, ...] | None = None) -> list[tuple[dict, dict]]:
        out = []
        for r in self.by_target.get((rel_type, target), []):
            src = self.by_id[r["source_ref"]]
            if types is None or src["type"] in types:
                out.append((src, r))
        return out

    def _targets(self, rel_type: str, source: str, types: tuple[str, ...] | None = None) -> list[tuple[dict, dict]]:
        out = []
        for r in self.by_source.get((rel_type, source), []):
            tgt = self.by_id[r["target_ref"]]
            if types is None or tgt["type"] in types:
                out.append((tgt, r))
        return out

    # ---- analíticas de una estrategia de detección
    def _analytic_lines(self, strategy: dict, with_details: bool = True) -> list[str]:
        lines = []
        for an_id in strategy.get("x_mitre_analytic_refs", []):
            an = self.analytics.get(an_id)
            if not an:
                continue
            aid, _ = _attack_ref(an)
            plats = ", ".join(an.get("x_mitre_platforms", []))
            line = f"{aid or an['name']}" + (f" [{plats}]" if plats else "") + f": {_clean(an.get('description'))}"
            if with_details:
                sources = sorted({ls.get("name", "") for ls in an.get("x_mitre_log_source_references", []) if ls.get("name")})
                if sources:
                    line += f" (log sources: {', '.join(sources)})"
                mutable = [f"{m.get('field')} - {m.get('description')}" for m in an.get("x_mitre_mutable_elements", [])]
                if mutable:
                    line += " | tunable elements: " + "; ".join(mutable)
            lines.append(line)
        return lines

    # ---- construcción de documentos
    def build(self) -> list[Document]:
        docs: list[Document] = []
        for obj in self.by_id.values():
            builder = getattr(self, f"_doc_{obj['type'].replace('-', '_')}", None)
            if builder is None:
                continue
            body = builder(obj)
            aid, url = _attack_ref(obj)
            label = TYPE_LABELS[obj["type"]]
            if obj["type"] == "attack-pattern" and obj.get("x_mitre_is_subtechnique"):
                label = "sub-technique"
            title = f"{aid} - {obj['name']}" if aid else obj["name"]
            header = (
                f"# {title}\n"
                f"Type: {label} | Domain: {self.domain}"
                + (f" | ATT&CK version: {self.version}" if self.version else "")
                + "\n"
            )
            docs.append(
                Document(
                    id=obj["id"],
                    title=title,
                    text=header + body,
                    metadata={
                        "doc_id": obj["id"],
                        "attack_id": aid,
                        "name": obj["name"],
                        "object_type": label,
                        "stix_type": obj["type"],
                        "domain": self.domain,
                        "attack_version": self.version,
                        "url": url,
                        "tactics": _tactics(obj),
                        "platforms": obj.get("x_mitre_platforms", []),
                        "source": "mitre-attack",
                    },
                )
            )
        return docs

    def _doc_attack_pattern(self, o: dict) -> str:
        parts = []
        parent = self._targets("subtechnique-of", o["id"])
        meta = [
            f"Tactics: {', '.join(_tactics(o)) or 'n/a'}",
            f"Platforms: {', '.join(o.get('x_mitre_platforms', [])) or 'n/a'}",
        ]
        if parent:
            meta.append(f"Sub-technique of: {_label(parent[0][0])}")
        subs = self._sources("subtechnique-of", o["id"])
        parts.append("\n".join(meta))
        parts.append(f"## Description\n{_clean(o.get('description'))}")
        if o.get("x_mitre_detection"):
            parts.append(f"## Detection\n{_clean(o['x_mitre_detection'])}")
        strategies = self._sources("detects", o["id"], ("x-mitre-detection-strategy",))
        if strategies:
            lines = []
            for strat, _ in strategies:
                lines.append(f"- {_label(strat)}")
                lines.extend(f"  - {al}" for al in self._analytic_lines(strat, with_details=False))
            parts.append("## Detection strategies\n" + "\n".join(lines))
        detects = self._sources("detects", o["id"], ("x-mitre-data-component",))
        if detects:
            names = []
            for comp, _ in detects:
                ds = self.by_id.get(comp.get("x_mitre_data_source_ref", ""), {})
                names.append(f"{ds.get('name', '?')}: {comp['name']}" if ds else comp["name"])
            parts.append(f"## Data components (detects)\n{_bullets(sorted(set(names)))}")
        mitig = self._sources("mitigates", o["id"], ("course-of-action",))
        if mitig:
            parts.append(
                "## Mitigations\n"
                + _bullets([f"{_label(m)}: {_clean(r.get('description')) or _clean(m.get('description'))[:300]}" for m, r in mitig])
            )
        if subs:
            parts.append("## Sub-techniques\n" + _bullets([_label(s) for s, _ in subs]))
        uses = self._sources("uses", o["id"], ("intrusion-set", "malware", "tool", "campaign"))
        if uses:
            examples = [f"{_label(s)} ({TYPE_LABELS[s['type']]}): {_clean(r.get('description'))}" for s, r in uses]
            parts.append(f"## Procedure examples\n{_bullets(examples, self.max_examples)}")
        return "\n\n".join(parts)

    def _doc_intrusion_set(self, o: dict) -> str:
        parts = [f"Aliases: {', '.join(o.get('aliases', [])) or 'n/a'}"]
        parts.append(f"## Description\n{_clean(o.get('description'))}")
        techs = self._targets("uses", o["id"], ("attack-pattern",))
        if techs:
            # Sólo ID + nombre: la descripción de la relación ya vive en la técnica ("Procedure examples")
            parts.append("## Techniques used\n" + _bullets(sorted(_label(t) for t, _ in techs)))
        sw = self._targets("uses", o["id"], ("malware", "tool"))
        if sw:
            parts.append("## Software used\n" + _bullets([_label(s) for s, _ in sw]))
        camps = self._sources("attributed-to", o["id"], ("campaign",))
        if camps:
            parts.append("## Campaigns\n" + _bullets([_label(c) for c, _ in camps]))
        return "\n\n".join(parts)

    def _doc_software(self, o: dict) -> str:
        parts = [
            f"Software type: {o['type']} | Aliases: {', '.join(o.get('x_mitre_aliases', [])) or 'n/a'} | "
            f"Platforms: {', '.join(o.get('x_mitre_platforms', [])) or 'n/a'}"
        ]
        parts.append(f"## Description\n{_clean(o.get('description'))}")
        techs = self._targets("uses", o["id"], ("attack-pattern",))
        if techs:
            # Sólo ID + nombre: la descripción de la relación ya vive en la técnica ("Procedure examples")
            parts.append("## Techniques used\n" + _bullets(sorted(_label(t) for t, _ in techs)))
        groups = self._sources("uses", o["id"], ("intrusion-set", "campaign"))
        if groups:
            parts.append("## Used by\n" + _bullets([_label(g) for g, _ in groups]))
        return "\n\n".join(parts)

    _doc_malware = _doc_software
    _doc_tool = _doc_software

    def _doc_course_of_action(self, o: dict) -> str:
        parts = [f"## Description\n{_clean(o.get('description'))}"]
        techs = self._targets("mitigates", o["id"], ("attack-pattern",))
        if techs:
            # Sólo ID + nombre: la descripción de la relación ya vive en la técnica ("Mitigations")
            parts.append("## Techniques mitigated\n" + _bullets(sorted(_label(t) for t, _ in techs)))
        return "\n\n".join(parts)

    def _doc_x_mitre_tactic(self, o: dict) -> str:
        short = o.get("x_mitre_shortname")
        techs = sorted(
            _label(t)
            for t in self.by_id.values()
            if t["type"] == "attack-pattern" and not t.get("x_mitre_is_subtechnique") and short in _tactics(t)
        )
        parts = [f"Shortname: {short}", f"## Description\n{_clean(o.get('description'))}"]
        if techs:
            parts.append("## Techniques in this tactic\n" + _bullets(techs))
        return "\n\n".join(parts)

    def _doc_campaign(self, o: dict) -> str:
        parts = [
            f"Aliases: {', '.join(o.get('aliases', [])) or 'n/a'} | "
            f"First seen: {str(o.get('first_seen', 'n/a'))[:10]} | Last seen: {str(o.get('last_seen', 'n/a'))[:10]}"
        ]
        parts.append(f"## Description\n{_clean(o.get('description'))}")
        groups = self._targets("attributed-to", o["id"], ("intrusion-set",))
        if groups:
            parts.append("## Attributed to\n" + _bullets([_label(g) for g, _ in groups]))
        techs = self._targets("uses", o["id"], ("attack-pattern",))
        if techs:
            # Sólo ID + nombre: la descripción de la relación ya vive en la técnica ("Procedure examples")
            parts.append("## Techniques used\n" + _bullets(sorted(_label(t) for t, _ in techs)))
        sw = self._targets("uses", o["id"], ("malware", "tool"))
        if sw:
            parts.append("## Software used\n" + _bullets([_label(s) for s, _ in sw]))
        return "\n\n".join(parts)

    def _doc_x_mitre_data_source(self, o: dict) -> str:
        comps = sorted(
            c["name"]
            for c in self.by_id.values()
            if c["type"] == "x-mitre-data-component" and c.get("x_mitre_data_source_ref") == o["id"]
        )
        parts = [
            f"Platforms: {', '.join(o.get('x_mitre_platforms', [])) or 'n/a'} | "
            f"Collection layers: {', '.join(o.get('x_mitre_collection_layers', [])) or 'n/a'}",
            f"## Description\n{_clean(o.get('description'))}",
        ]
        if comps:
            parts.append("## Data components\n" + _bullets(comps))
        return "\n\n".join(parts)

    def _doc_x_mitre_data_component(self, o: dict) -> str:
        ds = self.by_id.get(o.get("x_mitre_data_source_ref", ""), {})
        parts = [
            f"Data source: {_label(ds) if ds else 'n/a'} | Platforms: {', '.join(o.get('x_mitre_platforms', [])) or 'n/a'}",
            f"## Description\n{_clean(o.get('description'))}",
        ]
        # ATT&CK <= v17: relación directa data-component -detects-> technique
        techs = self._targets("detects", o["id"], ("attack-pattern",))
        if techs:
            parts.append("## Detects techniques\n" + _bullets([_label(t) for t, _ in techs]))
        # ATT&CK >= v18: usado como log source por analíticas de estrategias de detección
        strat_ids = self.dc_usage.get(o["id"], set())
        if strat_ids:
            detected = set()
            for sid in strat_ids:
                for t, _ in self._targets("detects", sid, ("attack-pattern",)):
                    detected.add(_label(t))
            parts.append(
                f"## Used as log source in {len(strat_ids)} detection strategies covering techniques\n"
                + _bullets(sorted(detected), self.max_examples * 4)
            )
        return "\n\n".join(parts)

    def _doc_x_mitre_detection_strategy(self, o: dict) -> str:
        parts = []
        techs = self._targets("detects", o["id"], ("attack-pattern",))
        if techs:
            parts.append("## Detects techniques\n" + _bullets([_label(t) for t, _ in techs]))
        analytics = self._analytic_lines(o, with_details=True)
        if analytics:
            parts.append("## Analytics\n" + _bullets(analytics))
        if o.get("description"):
            parts.insert(0, f"## Description\n{_clean(o['description'])}")
        return "\n\n".join(parts) or "(no details)"


def build_documents(objects: list[dict], domain: str, max_examples: int = 25) -> tuple[list[Document], str | None]:
    builder = MitreCorpusBuilder(objects, domain, max_examples)
    return builder.build(), builder.version
