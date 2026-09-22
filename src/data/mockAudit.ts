import type { AuditRecord } from '../types/audit'

export const PRIVACY_DISCLAIMER =
  'NeuroAudit estimates potential privacy exposure from neural data. Results are model-dependent and should not be interpreted as definitive statements about an individual\'s thoughts, emotions, identity, or medical condition.'

export const MOCK_AUDIT: AuditRecord = {
  auditName: 'Clinical cohort session A',
  fileName: 'session_a_rest_eeg.edf',
  analysisDate: '22 Aug 2026',
  status: 'Complete',
  overallRisk: 78,
  riskLevel: 'HIGH',
  overallSummary:
    'This demonstration audit estimates elevated overall privacy exposure, driven primarily by identity-related and stress-related inference potential. Scores describe estimated exposure under the assessment model, not confirmed personal attributes.',
  executiveSummary:
    'The analyzed EEG recording shows an overall privacy risk score of 78 / 100 (High). Identity-related inference potential is the largest contributor, with stress-related inference also elevated. Emotion and mental-workload dimensions fall in a medium range. These estimates are demonstration values intended to illustrate the assessment interface.',
  keyFindings: [
    'Identity-related inference shows the highest estimated privacy exposure in this audit.',
    'Stress-related inference also indicates elevated potential exposure.',
    'Emotion and mental-workload dimensions present moderate estimated exposure and remain model-dependent.',
  ],
  dimensions: [
    {
      key: 'identity',
      label: 'Identity',
      score: 85,
      level: 'HIGH',
      summary: 'Potential identity-related inference.',
      explanation:
        'Signal structure in this recording could support identity-related inference in some published models. This is an estimate of exposure, not a determination that a participant can be identified.',
      concern:
        'If raw EEG is retained with linking identifiers, estimated identity-related exposure remains high even when clinical labels are limited.',
    },
    {
      key: 'emotion',
      label: 'Emotion',
      score: 62,
      level: 'MEDIUM',
      summary: 'Potential emotion-related inference.',
      explanation:
        'Features associated with affective decoding literature could support emotion-related inference at a moderate estimated level. The audit does not classify an affective state.',
      concern:
        'Sharing minimally processed EEG beyond the original research purpose may increase estimated emotion-related exposure.',
    },
    {
      key: 'stress',
      label: 'Stress',
      score: 80,
      level: 'HIGH',
      summary: 'Potential stress-related inference.',
      explanation:
        'The recording contains characteristics that, depending on the model, could support stress-related inference. This is not a diagnosis or a confirmed stress measurement.',
      concern:
        'Access to channel-level data plus task context could raise estimated stress-related privacy exposure for participants.',
    },
    {
      key: 'workload',
      label: 'Mental Workload',
      score: 65,
      level: 'MEDIUM',
      summary: 'Potential cognitive workload inference.',
      explanation:
        'Estimated exposure for mental-workload inference is moderate. Workload-related models are task-sensitive and should not be read as a statement about a person’s cognitive capacity.',
      concern:
        'Combining EEG with performance logs could increase estimated workload-related exposure beyond what this file alone suggests.',
    },
  ],
  recommendations: [
    {
      id: 'restrict-raw',
      number: '01',
      title: 'Restrict Raw EEG Access',
      priority: 'HIGH',
      why: 'Channel-level recordings can retain more inference-relevant structure than derived summaries. Unrestricted internal access increases estimated exposure even when files are not public.',
      action:
        'Limit raw EEG access to named roles with a documented research need. Prefer derived features where the study protocol allows.',
    },
    {
      id: 'encrypt',
      number: '02',
      title: 'Encrypt Stored EEG Data',
      priority: 'HIGH',
      why: 'Stored recordings remain a long-lived privacy asset. Encryption at rest reduces the impact of unauthorized file access.',
      action:
        'Encrypt EEG at rest with managed keys, and encrypt transfers between acquisition, storage, and analysis environments.',
    },
    {
      id: 'pseudonymize',
      number: '03',
      title: 'Pseudonymize Participant Information',
      priority: 'HIGH',
      why: 'Direct identifiers combined with neural recordings raise estimated identity-related exposure. Separating identity keys from signal files is a standard research control.',
      action:
        'Store participant identifiers apart from EEG objects. Use study codes in filenames, metadata, and analysis workspaces.',
    },
    {
      id: 'retention',
      number: '04',
      title: 'Minimize Data Retention',
      priority: 'MEDIUM',
      why: 'Long retention extends the window in which stored neural data may be reused or accessed beyond the original purpose.',
      action:
        'Define retention aligned to the protocol and ethics approval. Remove or archive raw files when they are no longer required.',
    },
    {
      id: 'sharing',
      number: '05',
      title: 'Limit Unnecessary Data Sharing',
      priority: 'MEDIUM',
      why: 'Each additional recipient increases the chance of secondary use. Sharing should match the consent and the minimum data needed.',
      action:
        'Share the least identifiable form that still supports the collaboration. Record recipients, purpose, and expiry for each transfer.',
    },
  ],
  recentAudits: [
    {
      id: 'a1',
      name: 'Clinical cohort session A',
      date: '22 Aug 2026',
      fileName: 'session_a_rest_eeg.edf',
      risk: 78,
      level: 'HIGH',
      status: 'Complete',
    },
    {
      id: 'a2',
      name: 'Pilot study — rest-state',
      date: '18 Aug 2026',
      fileName: 'pilot_rest_02.edf',
      risk: 54,
      level: 'MEDIUM',
      status: 'Complete',
    },
    {
      id: 'a3',
      name: 'Workload dual-task trial',
      date: '09 Aug 2026',
      fileName: 'dual_task_block3.csv',
      risk: 41,
      level: 'MEDIUM',
      status: 'Complete',
    },
  ],
  disclaimer: PRIVACY_DISCLAIMER,
}

export const SCAN_STEPS = [
  'EEG file uploaded',
  'Signal loaded',
  'Preprocessing signal',
  'Feature extraction',
  'Privacy inference assessment',
  'Risk calculation',
  'Preparing audit results',
] as const
