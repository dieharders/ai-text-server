import { devDependencies } from '../package.json'

export const presets = [
  [
    'next/babel',
    {
      'preset-env': {
        targets: {
          electron: devDependencies.electron.replace(/^\^|~/, ''),
        },
      },
    },
  ],
]
