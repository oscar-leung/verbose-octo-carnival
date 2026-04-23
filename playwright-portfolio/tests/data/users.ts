export interface User {
  username: string;
  password: string;
  label: string;
}

export const USERS = {
  standard: {
    username: 'standard_user',
    password: 'secret_sauce',
    label: 'standard',
  },
  locked: {
    username: 'locked_out_user',
    password: 'secret_sauce',
    label: 'locked',
  },
  problem: {
    username: 'problem_user',
    password: 'secret_sauce',
    label: 'problem',
  },
  performanceGlitch: {
    username: 'performance_glitch_user',
    password: 'secret_sauce',
    label: 'performance_glitch',
  },
  visual: {
    username: 'visual_user',
    password: 'secret_sauce',
    label: 'visual',
  },
} as const satisfies Record<string, User>;
