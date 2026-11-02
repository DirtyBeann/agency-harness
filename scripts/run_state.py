#!/usr/bin/env python3
"""Fail-close binder: load workflows/*.states.json; refuse illegal transitions."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS, FLAGS_DIR = ROOT / "workflows", ROOT / "flags"
DEFAULT_VERDICTS, SCRIPTS = ROOT / "ledger" / "verdicts", ROOT / "scripts"
DEFAULT_STATE_DIR = ROOT / "ledger" / "state"
# Safe run ids for ledger/state/<run_id>.json paths (mirrors ledger run_id schema).
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,63}$")
# States only the human owner may enter, whatever the caller claims.
# Also treat any workflow state explicitly marked "owner_only": true as gated.
OWNER_GATED_STATES = {"LIVE_GO", "LIVE_NOGO"}
WORKFLOW_FILES = {
    "example-feature-branch": WORKFLOWS / "example-feature-branch.states.json",
    "example-ui-gauntlet": WORKFLOWS / "example-ui-gauntlet.states.json",
}
LEDGER_STATES = {
    "HOLD","SCOPE_LOCKED","ARCHITECT_READY","PLAN_APPROVED","APPLYING","VERIFY","REVIEW",
    "SKEPTIC","DEV_CANDIDATE","OWNER_TEST","LIVE_GO","LIVE_NOGO","SUB_DEAD","GOV_REVIEW",
    "ABORTED","FINAL_FAIL","ROUND_START","ROUND_END","OTHER",
}
STRICT_EDGES = {("REVIEW","SKEPTIC"), ("SKEPTIC","DEV_CANDIDATE")}

sys.path.insert(0, str(SCRIPTS))
import binder_rules  # shared: skeptic PASS evidence rule + secret patterns

def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_machine(workflow: str) -> dict[str, Any]:
    path = WORKFLOW_FILES.get(workflow)
    if path is None or not path.is_file():
        raise SystemExit(f"refused: unknown or missing workflow: {workflow}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or "transitions" not in data or "states" not in data:
        raise SystemExit(f"refused: bad states file: {getattr(path,'name',path)}")
    return data

def ledger_state_for(name: str) -> str:
    return name if name in LEDGER_STATES else "OTHER"

def truncate_notes(s: str, n: int = 240) -> str:
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 3] + "..."

def append_refuse_ledger(*, run_id, from_state, to_state, workflow, reason, dry_run):
    if dry_run:
        return None
    sys.path.insert(0, str(SCRIPTS))
    notes = truncate_notes(f"workflow={workflow} {from_state}->{to_state}: {reason}")
    event = {
        "schema": "LedgerEvent/v1", "run_id": run_id, "ts": now_ts(),
        "state": ledger_state_for(from_state), "event": "transition_refused",
        "lane": "platform" if workflow == "example-feature-branch" else "design",
        "role": "binder", "gateway": "unknown", "notes": notes,
    }
    try:
        import append_ledger  # type: ignore
        return str(append_ledger.append(event, run_id))
    except Exception as e:
        cmd = [
            sys.executable, str(SCRIPTS / "append_ledger.py"),
            "--run-id", run_id, "--state", ledger_state_for(from_state),
            "--event", "transition_refused",
            "--lane", "platform" if workflow == "example-feature-branch" else "design",
            "--role", "binder", "--gateway", "unknown",
            "--notes", truncate_notes(notes + f" import_fail={str(e)[:40]}"),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            sys.stderr.write(f"binder: ledger append failed: {p.stderr or p.stdout}\n")
            return None
        return (p.stdout or "").strip() or None

def find_legal_edge(machine, from_state, to_state):
    for t in machine.get("transitions", []):
        if t.get("to") == to_state and t.get("from") in (from_state, "*"):
            return t
    return None

def find_by_when(machine, from_state, when):
    return [t for t in machine.get("transitions", [])
            if t.get("when") == when and t.get("from") in (from_state, "*")]

def illegal_hit(machine, from_state, to_state):
    for item in machine.get("illegal_transitions", []):
        if item.get("from") == from_state and item.get("to") == to_state:
            # Conditional rows (when_forbidden) enforced by strict gates.
            if "when_forbidden" in item:
                continue
            return item
    return None

def forbidden_land(to_state, when):
    blob = f"{to_state} {when or ''}".lower()
    needles = ("merge_to_main","merge_to_master","land_main","land_master","to_main","to_master")
    if any(x in blob for x in needles) or to_state in ("main", "master"):
        return "forbidden: never land main/master (owner only via OWNER_TEST)"
    return None

def run_gate_review(verdicts_dir, review_path, security_path):
    cmd = [sys.executable, str(SCRIPTS / "gate_review.py"), "--verdicts-dir", str(verdicts_dir)]
    if review_path: cmd += ["--review-path", review_path]
    if security_path: cmd += ["--security-path", security_path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or p.stderr or "").strip() or f"gate_review rc={p.returncode}"

def check_skeptic_pass(skeptic_path: Path):
    if not skeptic_path.is_file():
        return False, f"missing SkepticVerdict: {skeptic_path.name}"
    try:
        data = json.loads(skeptic_path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return False, f"invalid SkepticVerdict parse: {e}"
    if data.get("schema") != "SkepticVerdict/v1":
        return False, "SkepticVerdict schema must be SkepticVerdict/v1"
    if data.get("verdict") != "PASS":
        return False, f"SkepticVerdict.verdict=={data.get('verdict')!r} (need PASS for DEV_CANDIDATE)"
    # Native false-pass rule (fixture 01): run before schema validation so the
    # refusal reason always names PASS and evidence.
    ok, why = binder_rules.skeptic_pass_ok(data)
    if not ok:
        return False, why
    p = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_verdict.py"), "--kind", "skeptic", "--file", str(skeptic_path)],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        return False, (p.stdout or p.stderr or "skeptic validate failed").strip()
    return True, "ok: SkepticVerdict.verdict==PASS with evidence"

def next_edges(machine, from_state):
    out = []
    for t in machine.get("transitions", []):
        if t.get("from") in (from_state, "*"):
            out.append({"from": from_state if t.get("from") == "*" else t.get("from"),
                        "to": t.get("to", ""), "when": t.get("when", "")})
    return out


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_RE.match(run_id):
        raise SystemExit(
            "refused: --run-id must match ^[A-Za-z0-9][A-Za-z0-9_.:-]{7,63}$ "
            "(safe chars only; it is used in ledger/state paths)"
        )


def is_owner_gated(machine, to_state: str) -> bool:
    if to_state in OWNER_GATED_STATES:
        return True
    st = (machine.get("states", {}) or {}).get(to_state) or {}
    return st.get("owner_only") is True


def read_recorded_state(state_dir: Path, run_id: str):
    p = state_dir / f"{run_id}.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"run_id": run_id, "state": "<corrupt>", "corrupt": True}


def write_recorded_state(state_dir: Path, run_id: str, workflow: str, from_state: str, to_state: str) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "RunState/v1",
        "run_id": run_id,
        "workflow": workflow,
        "from": from_state,
        "state": to_state,
        "ts": now_ts(),
    }
    (state_dir / f"{run_id}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def owner_gate_reason(machine, *, args, state_dir, from_state, to_state, run_id):
    """Proof required for LIVE_GO / LIVE_NOGO (and owner_only states).

    A caller claiming --from OWNER_TEST proves nothing: the run must have a
    recorded OWNER_TEST state for this run id, plus an owner approval artifact
    (OwnerApproval/v1) whose decision matches the target. Checked even in
    --dry-run because absence of proof is not a dry-run artifact.
    """
    if not args.run_id:
        return (f"owner-gated transition to {to_state} requires --run-id with a "
                "recorded OWNER_TEST state (a --from claim alone is not proof)")
    rec = read_recorded_state(state_dir, run_id)
    if not isinstance(rec, dict) or rec.get("state") != "OWNER_TEST":
        return (f"owner-gated transition to {to_state} requires a recorded OWNER_TEST "
                f"state for run {run_id} (ledger/state/{run_id}.json missing or not OWNER_TEST); "
                "a caller claim of --from OWNER_TEST is not proof")
    want = "GO" if to_state == "LIVE_GO" else "NOGO"
    approval = Path(args.verdicts_dir) / f"owner-approval-{run_id}.json"
    if not approval.is_file():
        return (f"owner-gated transition to {to_state} requires an owner approval artifact "
                f"{approval.name} (schema OwnerApproval/v1, run_id {run_id}, decision {want})")
    try:
        data = json.loads(approval.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return f"invalid owner approval artifact {approval.name}: {e}"
    if not isinstance(data, dict) or data.get("schema") != "OwnerApproval/v1":
        return f"owner approval artifact {approval.name} schema must be OwnerApproval/v1"
    if data.get("run_id") != run_id:
        return f"owner approval artifact {approval.name} run_id mismatch (want {run_id})"
    if data.get("decision") != want:
        return (f"owner approval artifact {approval.name} decision must be {want} for "
                f"{to_state} (got {data.get('decision')!r})")
    return None

def refuse(*, reason, from_state, to_state, workflow, run_id, dry_run, code=1):
    ledger_path = append_refuse_ledger(
        run_id=run_id, from_state=from_state, to_state=to_state,
        workflow=workflow, reason=reason, dry_run=dry_run,
    )
    print(json.dumps({"allowed": False, "from": from_state, "to": to_state,
                      "workflow": workflow, "reason": reason, "ledger": ledger_path},
                     ensure_ascii=False))
    raise SystemExit(code)

def allow(from_state, to_state, workflow, when=None):
    payload = {"allowed": True, "from": from_state, "to": to_state, "workflow": workflow}
    if when: payload["when"] = when
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(0)

def main() -> None:
    ap = argparse.ArgumentParser(description="Fail-close state binder")
    ap.add_argument("--workflow", required=True, choices=sorted(WORKFLOW_FILES))
    ap.add_argument("--from", dest="from_state", default="")
    ap.add_argument("--to", dest="to_state", default="")
    ap.add_argument("--transition", dest="when", default="")
    ap.add_argument("--strict", default=True, action=argparse.BooleanOptionalAction,
                    help="dev-only. Verdict gates on REVIEW->SKEPTIC and SKEPTIC->DEV_CANDIDATE "
                         "always run; --no-strict is refused on those gated transitions")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--flags-dir", default=str(FLAGS_DIR))
    ap.add_argument("--verdicts-dir", default=str(DEFAULT_VERDICTS))
    ap.add_argument("--ledger-state-dir", default=str(DEFAULT_STATE_DIR),
                    help=f"Recorded run state directory (default: {DEFAULT_STATE_DIR})")
    ap.add_argument("--review-path", default="")
    ap.add_argument("--security-path", default="")
    ap.add_argument("--skeptic-path", default="")
    ap.add_argument("--list-next", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-pause-to-paused", action="store_true")
    args = ap.parse_args()

    machine = load_machine(args.workflow)
    states = machine.get("states", {})

    if args.list_next:
        if not args.from_state:
            raise SystemExit("refused: --list-next requires --from")
        print(json.dumps({"from": args.from_state, "workflow": args.workflow,
                          "next": next_edges(machine, args.from_state)}, ensure_ascii=False))
        raise SystemExit(0)

    from_state, to_state, when = args.from_state, args.to_state, (args.when or None)

    if args.when:
        if not from_state:
            raise SystemExit("refused: --transition requires --from")
        hits = find_by_when(machine, from_state, args.when)
        run_id = args.run_id or f"binder-{args.workflow}-{now_ts().replace(':','')}"
        if len(run_id) < 8: run_id = (run_id + "-xxxxxxxx")[:16]
        if args.run_id:
            validate_run_id(args.run_id)
        if not hits:
            refuse(reason=f"no transition with when={args.when!r} from {from_state}",
                   from_state=from_state or "OTHER", to_state=to_state or "OTHER",
                   workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)
        if to_state:
            hits = [h for h in hits if h.get("to") == to_state]
            if not hits:
                refuse(reason=f"when={args.when!r} does not lead to {to_state}",
                       from_state=from_state, to_state=to_state,
                       workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)
        else:
            tos = {h.get("to") for h in hits}
            if len(tos) != 1:
                raise SystemExit(f"refused: when={args.when!r} ambiguous from {from_state}; pass --to")
            to_state = hits[0].get("to")
        when = args.when

    if not from_state or not to_state:
        raise SystemExit("refused: require --from and --to (or --from and --transition)")

    run_id = args.run_id or f"binder-{args.workflow}-{now_ts().replace(':','')}"
    if len(run_id) < 8: run_id = (run_id + "-xxxxxxxx")[:16]
    if args.run_id:
        validate_run_id(args.run_id)

    if from_state not in states and from_state != "*":
        refuse(reason=f"unknown from state: {from_state}", from_state="OTHER",
               to_state=to_state if to_state in LEDGER_STATES else "OTHER",
               workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)
    if to_state not in states:
        refuse(reason=f"unknown to state: {to_state}",
               from_state=from_state if from_state in LEDGER_STATES else "OTHER",
               to_state="OTHER", workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    land = forbidden_land(to_state, when)
    if land:
        refuse(reason=land, from_state=from_state, to_state=to_state,
               workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    # Kill switch: the canonical repo flags/PAUSE is ALWAYS checked; --flags-dir
    # only adds an extra location, it can never mask the canonical one.
    flags_dir = Path(args.flags_dir)
    pause_present = (flags_dir / "PAUSE").is_file() or (FLAGS_DIR / "PAUSE").is_file()
    if pause_present:
        if to_state == "PAUSED" and (args.allow_pause_to_paused or args.workflow == "example-ui-gauntlet"):
            edge = find_legal_edge(machine, from_state, "PAUSED")
            if edge is None:
                refuse(reason="flags/PAUSE present but no legal edge to PAUSED",
                       from_state=from_state, to_state=to_state,
                       workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)
            record_and_allow(args, run_id, from_state, to_state, when=edge.get("when"))
        refuse(reason="flags/PAUSE present: refuse mutate / treat as PAUSED (checked --flags-dir and canonical flags/)",
               from_state=from_state, to_state=to_state,
               workflow=args.workflow, run_id=run_id, dry_run=args.dry_run, code=10)

    hit = illegal_hit(machine, from_state, to_state)
    if hit:
        refuse(reason=hit.get("reason") or f"illegal_transitions: {from_state}->{to_state}",
               from_state=from_state, to_state=to_state,
               workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    edge = find_legal_edge(machine, from_state, to_state)
    if edge is None:
        refuse(reason=f"not in transitions list: {from_state}->{to_state}",
               from_state=from_state, to_state=to_state,
               workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    # Recorded run state: with --run-id, the binder keeps the last allowed
    # state on disk and refuses a --from that contradicts it.
    state_dir = Path(args.ledger_state_dir)
    if args.run_id:
        rec = read_recorded_state(state_dir, run_id)
        if isinstance(rec, dict) and rec.get("state") != from_state:
            refuse(reason=(f"recorded run state for {run_id} is {rec.get('state')!r}, "
                           f"not {from_state!r} (ledger/state/{run_id}.json)"),
                   from_state=from_state, to_state=to_state,
                   workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    # Owner gate: LIVE_GO / LIVE_NOGO (and owner_only states) need proof, not a claim.
    if is_owner_gated(machine, to_state):
        reason = owner_gate_reason(machine, args=args, state_dir=state_dir,
                                   from_state=from_state, to_state=to_state, run_id=run_id)
        if reason:
            refuse(reason=reason, from_state=from_state, to_state=to_state,
                   workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    # Verdict gates on strict edges ALWAYS run; --no-strict cannot bypass them.
    if (from_state, to_state) in STRICT_EDGES:
        if not args.strict:
            refuse(reason=("--no-strict is not allowed on gated transitions: "
                           f"{from_state}->{to_state} always runs verdict gates"),
                   from_state=from_state, to_state=to_state,
                   workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)
        vdir = Path(args.verdicts_dir)
        if (from_state, to_state) == ("REVIEW", "SKEPTIC"):
            rc, msg = run_gate_review(vdir, args.review_path, args.security_path)
            if rc == 2:
                refuse(reason=f"REVIEW->SKEPTIC blocked (escalate): {msg}",
                       from_state=from_state, to_state=to_state,
                       workflow=args.workflow, run_id=run_id, dry_run=args.dry_run, code=2)
            if rc != 0:
                refuse(reason=f"REVIEW->SKEPTIC fail-closed: {msg}",
                       from_state=from_state, to_state=to_state,
                       workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)
        if (from_state, to_state) == ("SKEPTIC", "DEV_CANDIDATE"):
            sk = Path(args.skeptic_path) if args.skeptic_path else vdir / "latest-skeptic.json"
            ok, msg = check_skeptic_pass(sk)
            if not ok:
                refuse(reason=f"SKEPTIC->DEV_CANDIDATE fail-closed: {msg}",
                       from_state=from_state, to_state=to_state,
                       workflow=args.workflow, run_id=run_id, dry_run=args.dry_run)

    record_and_allow(args, run_id, from_state, to_state, when=when or edge.get("when"))


def record_and_allow(args, run_id, from_state, to_state, when=None) -> None:
    """Record the new run state (when enabled), then allow the transition."""
    if args.run_id and not args.dry_run:
        write_recorded_state(Path(args.ledger_state_dir), run_id, args.workflow, from_state, to_state)
    allow(from_state, to_state, args.workflow, when=when)

if __name__ == "__main__":
    main()
