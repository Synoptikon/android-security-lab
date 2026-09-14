# FRP Emulator — Architecture v0.3

## Scope

Controlled-simulator-only. The emulator models Android security states and synthetic vulnerability scenarios. It does not implement an operational FRP bypass, Google-account evasion, or interaction with third-party devices.

## Logical architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         UI / CLI                             │
│ Android version │ Device model │ Lock mode │ Scenario       │
└────────────────────────────┬─────────────────────────────────┘
                             │ commands
┌────────────────────────────▼─────────────────────────────────┐
│                    Scenario Orchestrator                     │
│ setup → transition → observe → inject synthetic fault       │
│ → assert invariant → capture evidence                        │
└───────────────┬───────────────────────┬──────────────────────┘
                │                       │
     ┌──────────▼──────────┐  ┌────────▼─────────────┐
     │ Profile Registry    │  │ State Machine        │
     │ AndroidProfile      │  │ LOCKED               │
     │ DeviceProfile       │  │ RESET_PENDING        │
     │ PolicyProfile       │  │ FRP_LOCKED           │
     └──────────┬──────────┘  │ AUTHENTICATED        │
                │             └────────┬─────────────┘
                │                      │ transitions
     ┌──────────▼──────────────────────▼─────────────────────┐
     │                 Policy / Invariant Engine              │
     │ preconditions │ allowed transitions │ forbidden paths │
     │ lock-state integrity │ auth-state integrity            │
     └──────────────────────────┬─────────────────────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │ Evidence + Audit Layer      │
                 │ events │ hashes │ manifests │
                 │ results │ reproducibility   │
                 └─────────────────────────────┘
```

## Core domains

### 1. Android profiles

A version profile describes simulated platform behavior, not a real firmware image. Initial catalog: Android 8, 9, 10, 11, 12, 13, 14, 15 and an extensible slot for newer releases.

Fields: `profile_id`, `android_version`, `api_level`, `setup_wizard_profile`, `policy_profile`.

### 2. Device profiles

Device models are simulation identities. A profile may represent families such as Pixel, Samsung, Xiaomi, Motorola or ZTE without embedding vendor firmware or vendor-specific bypass procedures.

Fields: `device_id`, `manufacturer`, `model`, `screen_profile`, `android_profile_id`.

### 3. Lock and FRP state machine

Canonical lifecycle:

`DEVICE_READY → LOCKED → RESET_PENDING → FRP_LOCKED → AUTHENTICATED`

Lock variants: `PATTERN`, `PIN`, `PASSWORD`, `GOOGLE_ACCOUNT_REQUIRED`.

The invariant engine must reject impossible transitions and record the rejection as evidence.

### 4. Synthetic vulnerability lab

Scenarios model classes of implementation defects rather than real exploitation chains:

- `VULN-001` Intent validation
- `VULN-002` Activity exposure
- `VULN-003` Lock-state validation
- `VULN-004` Reset-state transition integrity
- `VULN-005` Authentication-state confusion
- `VULN-006` Privilege-boundary validation

Each scenario has: preconditions, affected simulated profile, initial state, test action, expected result, invariant, evidence and mitigation.

### 5. Evidence and audit

Every run produces deterministic artifacts where possible: event trace, scenario result, evidence record, audit result and reproducibility manifest. Artifacts must include the source commit when executed in CI.

## Boundary

No component may expose a procedure that converts a simulated weakness into a real-device FRP bypass. Real Android/Google authentication is outside the simulator boundary.
