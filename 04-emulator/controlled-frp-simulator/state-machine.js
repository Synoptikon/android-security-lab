const SetupWizardMachine = (() => {
  const phases = ['WELCOME', 'NETWORK', 'ACCOUNT_GATE', 'RESTORE_CHECK', 'FINISHED'];
  const transitions = Object.freeze({
    WELCOME: ['NETWORK'],
    NETWORK: ['ACCOUNT_GATE'],
    ACCOUNT_GATE: ['RESTORE_CHECK'],
    RESTORE_CHECK: ['FINISHED'],
    FINISHED: []
  });

  function initialState() {
    return {
      phase: 'WELCOME',
      provisioning: 'PROVISIONED',
      frp: 'ACTIVE',
      adb: 'UNAUTHORIZED',
      bootloader: 'LOCKED',
      result: 'BLOCKED'
    };
  }

  function transition(state, action = 'NEXT') {
    if (action !== 'NEXT') return { ...state, error: 'INVALID_ACTION' };
    const allowed = transitions[state.phase] || [];
    if (!allowed.length) return { ...state, error: 'NO_TRANSITION' };
    const next = allowed[0];
    return {
      ...state,
      phase: next,
      result: next === 'ACCOUNT_GATE' ? 'BLOCKED' : 'IN_PROGRESS',
      error: null
    };
  }

  function validate(state) {
    const errors = [];
    if (!phases.includes(state.phase)) errors.push('PHASE_INVALID');
    if (state.frp !== 'ACTIVE') errors.push('FRP_POLICY_CHANGED');
    if (state.adb !== 'UNAUTHORIZED') errors.push('ADB_AUTHORIZATION_CHANGED');
    if (state.bootloader !== 'LOCKED') errors.push('BOOTLOADER_POLICY_CHANGED');
    if (state.phase === 'ACCOUNT_GATE' && state.result !== 'BLOCKED') errors.push('ACCOUNT_GATE_NOT_BLOCKED');
    return { valid: errors.length === 0, errors };
  }

  return Object.freeze({ phases, transitions, initialState, transition, validate });
})();
